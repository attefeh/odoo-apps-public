# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class TranslationLoader(models.TransientModel):
    _name = 'translation.loader'
    _description = 'Load Translated Terms'

    def _default_langs(self):
        return self.env['res.lang'].search(
            [('active', '=', True), ('code', '!=', 'en_US')])

    scope = fields.Selection(
        [('all', 'All installed modules'), ('filter', 'Selected models / modules')],
        string='Scope', default='all', required=True)
    lang_ids = fields.Many2many(
        'res.lang', string='Languages', default=_default_langs,
        domain=[('active', '=', True)], required=True)
    load_db = fields.Boolean(
        string='Field, View & Menu translations', default=True,
        help="Translatable model fields, view architectures (buttons/menus/"
             "labels), action names, selection labels, email templates, ...")
    load_code = fields.Boolean(
        string='Code translations (errors / JS)', default=True,
        help="Python messages and web/JavaScript strings from the modules' "
             ".po files.")
    model_ids = fields.Many2many(
        'ir.model', string='Models',
        help="Limit database terms to these models (Filtered scope).")
    module_ids = fields.Many2many(
        'ir.module.module', string='Modules',
        domain=[('state', '=', 'installed')],
        help="Limit code terms to these modules (Filtered scope).")
    record_limit = fields.Integer(
        string='Max records per model', default=0,
        help="0 = no limit. Cap the number of records scanned per model to "
             "keep loading fast on large databases.")
    purge_first = fields.Boolean(
        string='Clear existing terms first', default=True)

    def action_load(self):
        self.ensure_one()
        if not self.load_db and not self.load_code:
            raise UserError(_("Select at least one kind of term to load."))
        lang_codes = self.lang_ids.mapped('code')
        model_names = self.model_ids.mapped('model') if self.scope == 'filter' else None
        module_names = self.module_ids.mapped('name') if self.scope == 'filter' else None

        counts = self.env['translation.term'].load_terms(
            lang_codes=lang_codes,
            model_names=model_names,
            module_names=module_names,
            load_db=self.load_db,
            load_code=self.load_code,
            record_limit=self.record_limit,
            purge=self.purge_first,
        )

        action = self.env['ir.actions.act_window']._for_xml_id(
            'translation_manager.action_translation_term')
        action['context'] = {'search_default_to_translate': 0}
        action['help'] = _(
            "Loaded %(db)s field/view terms and %(code)s code terms.",
            db=counts.get('db', 0), code=counts.get('code', 0))
        return action
