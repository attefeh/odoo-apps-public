from odoo import _, api, fields, models
from odoo.exceptions import RedirectWarning, UserError


class ResCurrency(models.Model):
    _inherit = "res.currency"

    rate_guard_required = fields.Boolean(
        string="Require Daily Rate",
        help="If set, posting/confirming any document in this currency is "
             "blocked unless a currency rate exists for today.",
    )

    @api.model
    def _get_company_rate_for_date(self, currency, company, date):
        """Return the ``company_rate`` effective for ``currency`` on ``date``
        for ``company`` (the most recent rate on or before that date), i.e. the
        rate that was actually applied for conversions at that time. Returns
        1.0 for the company currency and 0.0 when no rate is available."""
        if not currency or not date:
            return 0.0
        company = company or self.env.company
        if currency == company.currency_id:
            return 1.0
        rate = self.env["res.currency.rate"].sudo().search([
            ("currency_id", "=", currency.id),
            ("company_id", "=", company.id),
            ("name", "<=", date),
        ], order="name desc", limit=1)
        return rate.company_rate if rate else 0.0

    @api.model
    def _check_rate_for_date(self, currencies, date=None, company=None, resume=None):
        """Raise a RedirectWarning if any guarded currency lacks a rate for
        the given date. ``date`` falls back to today when not provided (e.g.
        a document whose date is only set on posting).

        ``resume`` (optional) is a dict ``{"model", "res_id", "method"}``
        describing the action the user was performing. It is forwarded to the
        quick-entry wizard so that, once the rate is saved, the original
        action (e.g. creating the payment) is replayed instead of being lost."""
        company = company or self.env.company
        date = date or fields.Date.context_today(self)
        guarded = currencies.filtered(
            lambda c: c.rate_guard_required and c.id != company.currency_id.id
        )
        if not guarded:
            return

        Rate = self.env["res.currency.rate"].sudo()
        for currency in guarded:
            exists = Rate.search_count([
                ("currency_id", "=", currency.id),
                ("company_id", "=", company.id),
                ("name", "=", date),
            ], limit=1)
            if exists:
                continue

            action = self.env.ref(
                "currency_rate_guard."
                "action_currency_rate_quick_entry_wizard"
            ).sudo().read()[0]
            action["context"] = {
                "default_currency_id": currency.id,
                "default_company_id": company.id,
                "default_date": date,
            }
            if resume:
                action["context"].update({
                    "default_resume_model": resume.get("model"),
                    "default_resume_res_id": resume.get("res_id"),
                    "default_resume_method": resume.get("method"),
                })
            raise RedirectWarning(
                _(
                    "No exchange rate has been registered for %(currency)s "
                    "on %(date)s. Please enter the rate for that date before "
                    "continuing."
                ) % {"currency": currency.name, "date": date},
                action,
                _("Enter Rate for %(date)s") % {"date": date},
            )


class ResCurrencyRate(models.Model):
    _inherit = "res.currency.rate"

    def _documents_using_rate(self):
        """Return a human-readable name of the first confirmed/posted document
        that relies on this rate line (same currency, company and date), or
        None if the rate line is free to change. A document is matched on the
        date the guard validates: payment.date, move.invoice_date and
        purchase.date_approve."""
        self.ensure_one()
        if not self.currency_id:
            return None
        company = self.company_id or self.env.company
        # The company-currency "rate" row (rate == 1) is never document-bound.
        if self.currency_id == company.currency_id:
            return None

        common = [
            ("currency_id", "=", self.currency_id.id),
            ("company_id", "=", company.id),
        ]

        payment = self.env["account.payment"].sudo().search(
            common + [
                ("state", "in", ("in_process", "paid")),
                ("date", "=", self.name),
            ], limit=1)
        if payment:
            return _("payment %s") % (payment.name or payment.display_name)

        move = self.env["account.move"].sudo().search(
            common + [
                ("state", "=", "posted"),
                ("invoice_date", "=", self.name),
            ], limit=1)
        if move:
            return _("invoice %s") % (move.name or move.display_name)

        # date_approve is a Datetime; match its date part to this rate's date.
        orders = self.env["purchase.order"].sudo().search(
            common + [
                ("state", "in", ("purchase", "done")),
                ("date_approve", "!=", False),
            ])
        order = orders.filtered(
            lambda o: fields.Date.to_date(o.date_approve) == self.name
        )[:1]
        if order:
            return _("purchase order %s") % (order.name or order.display_name)

        return None

    def _ensure_not_in_use(self):
        # The quick-entry wizard sets this flag: entering a rate through our
        # own flow must never be blocked. The protection only guards manual
        # edits/deletes from the currency rates list.
        if self.env.context.get("skip_rate_in_use_guard"):
            return
        for rate in self:
            doc = rate._documents_using_rate()
            if doc:
                raise UserError(_(
                    "The rate for %(currency)s on %(date)s is already used by "
                    "%(doc)s and can no longer be changed or removed. Delete "
                    "that document first if you need to modify this rate."
                ) % {
                    "currency": rate.currency_id.name,
                    "date": rate.name,
                    "doc": doc,
                })

    def write(self, vals):
        # Only the fields that affect a document's conversion are protected;
        # touching unrelated metadata stays allowed.
        protected = {"name", "currency_id", "company_id",
                     "rate", "company_rate", "inverse_company_rate"}
        if protected.intersection(vals):
            self._ensure_not_in_use()
        return super().write(vals)

    def unlink(self):
        self._ensure_not_in_use()
        return super().unlink()

