from odoo import models


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    def _create_payments(self):
        for wizard in self:
            wizard.env["res.currency"]._check_rate_for_date(
                wizard.currency_id,
                date=wizard.payment_date,
                company=wizard.company_id,
                resume={
                    "model": "account.payment.register",
                    "res_id": wizard.id,
                    "method": "action_create_payments",
                },
            )
        return super()._create_payments()
