from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    used_company_rate = fields.Float(
        string="Exchange Rate Used",
        digits=(16, 6),
        compute="_compute_used_company_rate",
        help="Company-currency exchange rate applied for this document's "
             "invoice date.",
    )

    @api.depends("currency_id", "company_id", "invoice_date")
    def _compute_used_company_rate(self):
        for move in self:
            move.used_company_rate = self.env["res.currency"]\
                ._get_company_rate_for_date(
                    move.currency_id, move.company_id, move.invoice_date)

    def _post(self, soft=True):
        for move in self:
            # Only invoices are keyed on invoice_date. Payment moves and other
            # journal entries have no invoice_date (which would wrongly fall
            # back to today); payments are guarded by their own hook.
            if not move.is_invoice(include_receipts=True):
                continue
            self.env["res.currency"]._check_rate_for_date(
                move.currency_id, date=move.invoice_date, company=move.company_id,
                resume={
                    "model": "account.move",
                    "res_id": move.id,
                    "method": "action_post",
                },
            )
        return super()._post(soft=soft)
