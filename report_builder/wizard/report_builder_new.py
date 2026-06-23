# -*- coding: utf-8 -*-
from odoo import _, fields, models

# Starter designs (plain HTML; the editor and compiler understand data-rb-*).
STARTERS = {
    'blank': '',
    'letter': (
        '<h2 data-rb-field="doc.name" data-rb-out="field">Title</h2>'
        '<p>Dear <span data-rb-field="doc.display_name">Customer</span>,</p>'
        '<p>Edit this text and drop fields, loops or conditions from the '
        'left panel.</p>'
    ),
    'table': (
        '<h2 data-rb-field="doc.name" data-rb-out="field">Title</h2>'
        '<table class="table">'
        '<thead><tr><th>Name</th></tr></thead>'
        '<tbody>'
        '<tr data-rb-foreach="" data-rb-as="line">'
        '<td data-rb-field="line.display_name">Line</td>'
        '</tr>'
        '</tbody></table>'
    ),
}


class ReportBuilderNew(models.TransientModel):
    _name = 'report.builder.new'
    _description = 'New Report Template'

    name = fields.Char(required=True, default="New Report")
    model_id = fields.Many2one('ir.model', string='Model', required=True,
                               ondelete='cascade')
    layout = fields.Selection(
        [('external', 'Company letterhead'),
         ('internal', 'Minimal header'),
         ('blank', 'Blank')],
        string='Layout', default='external', required=True)
    starter = fields.Selection(
        [('blank', 'Empty canvas'),
         ('letter', 'Letter / header fields'),
         ('table', 'Table over line items')],
        string='Starter', default='letter', required=True)
    paperformat_id = fields.Many2one('report.paperformat', string='Paper Format')

    def action_create_open(self):
        self.ensure_one()
        tmpl = self.env['report.builder.template'].create({
            'name': self.name,
            'model_id': self.model_id.id,
            'layout': self.layout,
            'paperformat_id': self.paperformat_id.id or False,
            'body_html': STARTERS.get(self.starter, ''),
        })
        return tmpl.action_open_editor()
