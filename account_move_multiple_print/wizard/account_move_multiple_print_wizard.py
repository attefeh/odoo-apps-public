import base64

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.pdf import merge_pdf


class AccountMoveMultiplePrintWizard(models.TransientModel):
    _name = "account.move.multiple.print.wizard"
    _description = "Account Move Multiple Print Wizard"

    move_id = fields.Many2one(
        "account.move",
        string="Invoice / Bill",
        required=True,
        default=lambda self: self._default_move_id(),
    )
    copies = fields.Integer(string="Number of Copies", default=1, required=True)

    @api.model
    def _default_move_id(self):
        if self.env.context.get("active_model") == "account.move":
            return self.env.context.get("active_id")
        return False

    def action_print(self):
        self.ensure_one()
        if self.copies < 1:
            raise UserError(_("Number of copies must be at least 1."))

        report = self.env.ref("account.account_invoices")
        pdf_content, _content_type = report._render_qweb_pdf(
            report.report_name, [self.move_id.id]
        )
        merged = merge_pdf([pdf_content] * self.copies)

        filename = "%s_x%d.pdf" % (
            (self.move_id.name or "Draft").replace("/", "_"),
            self.copies,
        )
        attachment = self.env["ir.attachment"].create({
            "name": filename,
            "type": "binary",
            "datas": base64.b64encode(merged),
            "mimetype": "application/pdf",
            "res_model": "account.move",
            "res_id": self.move_id.id,
        })
        return {
            "type": "ir.actions.act_url",
            "url": "/web/content/%d?download=true" % attachment.id,
            "target": "self",
        }
