from odoo import models


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        result = super().session_info()
        # Force-disable tours regardless of the stored res.users.tour_enabled
        # value or the current_tour record on web_tour.tour. The JS tour
        # service reads these from `session` at startup
        # (web_tour/static/src/js/tour_service.js:66, :269) and stays inert
        # when both are falsy.
        result["tour_enabled"] = False
        result["current_tour"] = False
        return result
