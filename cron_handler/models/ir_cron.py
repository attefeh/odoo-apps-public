from odoo import fields, models


class IrCron(models.Model):
    _inherit = 'ir.cron'

    handler_managed = fields.Boolean(
        string='Managed by Cron Handler',
        default=False,
        copy=False,
        help='Set automatically when a Cron Handler deactivates this scheduled '
             'action to take over its timing. The scheduled action is '
             're-activated once no active handler manages it anymore.',
    )
