from odoo import _, api, fields, models
from odoo.exceptions import UserError


class CurrencyRateQuickEntryWizard(models.TransientModel):
    _name = "currency.rate.quick.entry.wizard"
    _description = "Quick Entry for Today's Currency Rate"

    currency_id = fields.Many2one(
        "res.currency", string="Currency", required=True, readonly=True,
    )
    company_id = fields.Many2one(
        "res.company", string="Company", required=True,
        default=lambda self: self.env.company,
    )
    company_currency_id = fields.Many2one(
        related="company_id.currency_id", string="Company Currency", readonly=True,
    )
    date = fields.Date(
        string="Date", required=True, default=fields.Date.context_today,
    )
    # Action the user was performing when the guard interrupted them, so it
    # can be replayed once the rate is saved (e.g. finish creating a payment).
    resume_model = fields.Char()
    resume_res_id = fields.Integer()
    resume_method = fields.Char()
    company_rate = fields.Float(
        string="Rate",
        digits=(16, 6),
        required=True,
        default=lambda self: self._default_company_rate(),
        help="How many units of the selected currency equal 1 unit of the "
             "company currency (e.g. 1 OMR = X IRR).",
    )

    @api.model
    def _default_company_rate(self):
        """Pre-fill with the rate registered nearest (by date) to the target
        date for the same currency pair, so the user only has to adjust it."""
        ctx = self.env.context
        currency_id = ctx.get("default_currency_id")
        company_id = ctx.get("default_company_id") or self.env.company.id
        target = fields.Date.to_date(ctx.get("default_date")) \
            or fields.Date.context_today(self)
        if not currency_id:
            return 0.0

        Rate = self.env["res.currency.rate"].sudo()
        base = [
            ("currency_id", "=", currency_id),
            ("company_id", "=", company_id),
        ]
        # The closest rate on/before the date and the closest on/after it,
        # then keep whichever is nearer to the target date.
        before = Rate.search(
            base + [("name", "<=", target)], order="name desc", limit=1
        )
        after = Rate.search(
            base + [("name", ">", target)], order="name asc", limit=1
        )
        candidates = before + after
        if not candidates:
            return 0.0
        nearest = min(candidates, key=lambda r: abs((r.name - target).days))
        return nearest.company_rate

    @api.constrains("company_rate")
    def _check_rate_positive(self):
        for w in self:
            if w.company_rate <= 0:
                raise UserError(_("Rate must be strictly positive."))

    def action_save(self):
        self.ensure_one()
        # Saving a rate through our own wizard bypasses the in-use protection
        # (which only exists to block manual edits/deletes of used rates).
        Rate = self.env["res.currency.rate"].sudo().with_context(
            skip_rate_in_use_guard=True)
        existing = Rate.search([
            ("currency_id", "=", self.currency_id.id),
            ("company_id", "=", self.company_id.id),
            ("name", "=", self.date),
        ], limit=1)
        vals = {"company_rate": self.company_rate}
        if existing:
            existing.write(vals)
        else:
            Rate.create({
                "currency_id": self.currency_id.id,
                "company_id": self.company_id.id,
                "name": self.date,
                **vals,
            })

        # Replay the action the user was performing (e.g. create the payment)
        # now that the missing rate exists; the guard will pass this time.
        if self.resume_model and self.resume_method and self.resume_res_id:
            record = self.env[self.resume_model].browse(self.resume_res_id)
            if record.exists():
                return getattr(record, self.resume_method)()
        return {"type": "ir.actions.act_window_close"}
