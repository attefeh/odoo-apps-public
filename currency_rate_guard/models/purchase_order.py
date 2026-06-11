from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    used_company_rate = fields.Float(
        string="Exchange Rate Used",
        digits=(16, 6),
        compute="_compute_used_company_rate",
        help="Company-currency exchange rate applied for this order's "
             "approval date.",
    )

    @api.depends("currency_id", "company_id", "date_approve")
    def _compute_used_company_rate(self):
        for order in self:
            order.used_company_rate = self.env["res.currency"]\
                ._get_company_rate_for_date(
                    order.currency_id, order.company_id,
                    fields.Date.to_date(order.date_approve))

    def button_confirm(self):
        for order in self:
            # date_approve is a Datetime; the rate is keyed by Date.
            approve_date = fields.Date.to_date(order.date_approve)
            self.env["res.currency"]._check_rate_for_date(
                order.currency_id, date=approve_date, company=order.company_id,
                resume={
                    "model": "purchase.order",
                    "res_id": order.id,
                    "method": "button_confirm",
                },
            )
        return super().button_confirm()
