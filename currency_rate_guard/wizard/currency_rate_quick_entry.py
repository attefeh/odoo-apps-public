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
    inverse_company_rate = fields.Float(
        string="Rate",
        digits=(16, 6),
        required=True,
        help="How many units of the company currency equal 1 unit of the "
             "selected currency (e.g. 1 OMR = X IRR).",
    )

    @api.constrains("inverse_company_rate")
    def _check_rate_positive(self):
        for w in self:
            if w.inverse_company_rate <= 0:
                raise UserError(_("Rate must be strictly positive."))

    def action_save(self):
        self.ensure_one()
        Rate = self.env["res.currency.rate"].sudo()
        existing = Rate.search([
            ("currency_id", "=", self.currency_id.id),
            ("company_id", "=", self.company_id.id),
            ("name", "=", self.date),
        ], limit=1)
        vals = {"inverse_company_rate": self.inverse_company_rate}
        if existing:
            existing.write(vals)
        else:
            Rate.create({
                "currency_id": self.currency_id.id,
                "company_id": self.company_id.id,
                "name": self.date,
                **vals,
            })
        return {"type": "ir.actions.act_window_close"}
