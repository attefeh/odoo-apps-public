# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class TranslationLoader(models.TransientModel):
    _name = 'translation.loader'
    _description = 'Refresh Translated Terms'

    def _default_langs(self):
        return self.env['res.lang'].search(
            [('active', '=', True), ('code', '!=', 'en_US')])

    model_ids = fields.Many2many(
        'ir.model', string='Models',
        help="Limit to these models. Leave empty to load every model.")
    module_ids = fields.Many2many(
        'ir.module.module', string='Modules',
        domain=[('state', '=', 'installed')],
        help="Limit to these modules — both their field/view terms and their "
             "code terms. Leave empty to load every installed module.")
    lang_ids = fields.Many2many(
        'res.lang', string='Languages', default=_default_langs,
        domain=[('active', '=', True), ('code', '!=', 'en_US')],
        help="Languages to load. Leave empty to load every active language.")

    @api.model
    def action_open_loader(self):
        """Open the refresh wizard, but only when there is something to
        translate. With a single active language (the default English-only
        setup) there is no target language, so alert the user instead."""
        if self.env['res.lang'].search_count([('active', '=', True)]) <= 1:
            raise UserError(_(
                "Translation Manager needs more than one active language.\n\n"
                "Only English (en_US) is active right now, so there is nothing "
                "to translate yet. Activate at least one more language under "
                "Settings ‣ Translations ‣ Languages, then open this "
                "menu again."))
        return self.env['ir.actions.act_window']._for_xml_id(
            'translation_manager.action_translation_loader')

    def action_load(self):
        self.ensure_one()
        lang_codes = (self.lang_ids.mapped('code')
                      or self._default_langs().mapped('code'))
        counts = self.env['translation.term'].load_terms(
            lang_codes=lang_codes,
            model_names=self.model_ids.mapped('model') or None,
            module_names=self.module_ids.mapped('name') or None,
        )
        action = self.env['ir.actions.act_window']._for_xml_id(
            'translation_manager.action_translation_term')
        action['context'] = {
            'search_default_to_translate': 0,
            'search_default_group_lang': 1,
        }
        action['help'] = _(
            "Loaded %(db)s field/view terms and %(code)s code terms.",
            db=counts.get('db', 0), code=counts.get('code', 0))
        return action
