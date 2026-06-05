from odoo import api, models


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.depends("create_date")
    def _compute_tour_enabled(self):
        # Override the upstream compute (web_tour/models/res_users.py) so
        # newly created users never get tour_enabled=True. Existing users may
        # still have True stored from before install, but it doesn't matter:
        # session_info() in ir_http.py forces False on every page load.
        for user in self:
            user.tour_enabled = False

    @api.model
    def switch_tour_enabled(self, val):
        # The developer-tools "Onboarding" toggle calls this. Always force
        # False so the toggle can't re-enable tours.
        self.env.user.sudo().tour_enabled = False
        return False
