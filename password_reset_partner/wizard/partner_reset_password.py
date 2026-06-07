from odoo import models, fields, _
from odoo.exceptions import UserError


class PartnerResetPassword(models.TransientModel):
    _name = 'partner.reset.password'
    _description = 'Wizard to reset password for a partner'

    user_ids = fields.Many2many('res.users', string='Users', required=True, readonly=True)
    new_password = fields.Char(string='New Password')
    re_new_password = fields.Char(string='New Password (Retype)')

    def action_reset_password(self):
        # Validate the typed passwords, apply them to the selected users, and log the change on their partners.
        if not self.user_ids:
            raise UserError(_("No user selected for password reset."))
        if not self.new_password or not self.re_new_password:
            raise UserError(_("New password fields cannot be empty."))
        if self.new_password != self.re_new_password:
            raise UserError(_("The new passwords do not match."))
        self.user_ids.write({'password': self.new_password})
        for partner in self.user_ids.partner_id:
            partner.message_post(
                body=_("Password has been reset by %s", self.env.user.name)
            )
        return {'type': 'ir.actions.act_window_close'}
