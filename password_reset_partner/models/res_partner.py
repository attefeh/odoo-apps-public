from odoo import models, _
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def reset_user_password(self):
        # Open the password-reset wizard for the users linked to this partner.
        self.ensure_one()
        if not self.user_ids:
            raise UserError(_("This partner is not linked to any user."))
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'partner.reset.password',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_user_ids': [(6, 0, self.user_ids.ids)],
            },
        }
