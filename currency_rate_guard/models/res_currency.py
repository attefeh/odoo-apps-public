from odoo import _, api, fields, models
from odoo.exceptions import RedirectWarning


class ResCurrency(models.Model):
    _inherit = "res.currency"

    rate_guard_required = fields.Boolean(
        string="Require Daily Rate",
        help="If set, posting/confirming any document in this currency is "
             "blocked unless a currency rate exists for today.",
    )

    @api.model
    def _check_rate_for_today(self, currencies, company=None):
        """Raise a RedirectWarning if any guarded currency lacks a rate today. """
        company = company or self.env.company
        today = fields.Date.context_today(self)
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
                ("name", "=", today),
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
            }
            raise RedirectWarning(
                _(
                    "No exchange rate has been registered for %(currency)s "
                    "on %(date)s. Please enter today's rate before continuing."
                ) % {"currency": currency.name, "date": today},
                action,
                _("Enter Today's Rate"),
            )

