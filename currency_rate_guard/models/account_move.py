from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _post(self, soft=True):
        for move in self:
            self.env["res.currency"]._check_rate_for_today(
                move.currency_id, company=move.company_id
            )
        return super()._post(soft=soft)
