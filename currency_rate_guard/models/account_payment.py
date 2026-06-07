from odoo import models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def action_post(self):
        for payment in self:
            self.env["res.currency"]._check_rate_for_today(
                payment.currency_id, company=payment.company_id
            )
        return super().action_post()
