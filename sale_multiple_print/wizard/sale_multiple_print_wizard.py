import base64

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.pdf import merge_pdf


class SaleMultiplePrintWizard(models.TransientModel):
    _name = "sale.multiple.print.wizard"
    _description = "Sale Order Multiple Print Wizard"

    order_id = fields.Many2one(
        "sale.order",
        string="Sale Order",
        required=True,
        default=lambda self: self._default_order_id(),
    )
    copies = fields.Integer(string="Number of Copies", default=1, required=True)

    @api.model
    def _default_order_id(self):
        if self.env.context.get("active_model") == "sale.order":
            return self.env.context.get("active_id")
        return False

    def action_print(self):
        self.ensure_one()
        if self.copies < 1:
            raise UserError(_("Number of copies must be at least 1."))

        report = self.env.ref("sale.action_report_saleorder")
        pdf_content, _content_type = report._render_qweb_pdf(
            report.report_name, [self.order_id.id]
        )
        merged = merge_pdf([pdf_content] * self.copies)

        filename = "%s_x%d.pdf" % (self.order_id.name, self.copies)
        attachment = self.env["ir.attachment"].create({
            "name": filename,
            "type": "binary",
            "datas": base64.b64encode(merged),
            "mimetype": "application/pdf",
            "res_model": "sale.order",
            "res_id": self.order_id.id,
        })
        return {
            "type": "ir.actions.act_url",
            "url": "/web/content/%d?download=true" % attachment.id,
            "target": "self",
        }
