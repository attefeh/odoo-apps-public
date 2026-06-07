from odoo import models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def button_confirm(self):
        for order in self:
            self.env["res.currency"]._check_rate_for_today(
                order.currency_id, company=order.company_id
            )
        return super().button_confirm()
