from odoo import api, fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    used_company_rate = fields.Float(
        string="Exchange Rate Used",
        digits=(16, 6),
        compute="_compute_used_company_rate",
        help="Company-currency exchange rate applied for this payment's date.",
    )

    @api.depends("currency_id", "company_id", "date")
    def _compute_used_company_rate(self):
        for payment in self:
            payment.used_company_rate = self.env["res.currency"]\
                ._get_company_rate_for_date(
                    payment.currency_id, payment.company_id, payment.date)

    def action_post(self):
        for payment in self:
            self.env["res.currency"]._check_rate_for_date(
                payment.currency_id, date=payment.date, company=payment.company_id,
                resume={
                    "model": "account.payment",
                    "res_id": payment.id,
                    "method": "action_post",
                },
            )
        return super().action_post()
