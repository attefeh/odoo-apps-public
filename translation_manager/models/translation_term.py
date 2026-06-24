# -*- coding: utf-8 -*-
import hashlib
import logging

from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError

from . import code_translations_patch as ctp

_logger = logging.getLogger(__name__)

TERM_TYPES = [
    ('model', 'Field'),
    ('model_term', 'Field Term'),
    ('code_python', 'Server Code'),
    ('code_web', 'Web / JS Code'),
]

DB_TYPES = ('model', 'model_term')
CODE_TYPES = ('code_python', 'code_web')

# Stores the fingerprint of the translatable-field set so a registry reload can
# tell whether a module install/upgrade/uninstall changed what is translatable.
PARAM_FINGERPRINT = 'translation_manager.translatable_fields_fingerprint'


class TranslationTerm(models.Model):
    _name = 'translation.term'
    _description = 'Translation Term'
    _order = 'term_type, module, model_name, field_name, src, lang'
    _rec_name = 'src'

    term_type = fields.Selection(
        TERM_TYPES, string='Type', required=True, default='model', index=True)
    lang_id = fields.Many2one(
        'res.lang', string='Language', required=True, ondelete='cascade', index=True)
    lang = fields.Char(related='lang_id.code', store=True, index=True, readonly=True)

    module = fields.Char(string='Module', index=True)
    model_name = fields.Char(string='Model', index=True)
    field_name = fields.Char(string='Field')
    res_id = fields.Integer(string='Record ID')
    res_name = fields.Char(string='Record')

    src = fields.Text(string='Source Term (en_US)')
    value = fields.Text(string='Translation')

    state = fields.Selection(
        [('to_translate', 'To Translate'), ('translated', 'Translated')],
        string='Status', compute='_compute_state', store=True, index=True)
    is_override = fields.Boolean(
        string='Code Override', default=False, index=True,
        help="Set on code terms whose value was edited by a user; only these "
             "are served on top of the module .po files.")
    term_key = fields.Char(string='Key', index=True, copy=False)

    _sql_constraints = [
        ('term_key_uniq', 'unique(term_key)',
         'This translation term already exists for this language.'),
    ]

    # ------------------------------------------------------------------
    # Identity / computed
    # ------------------------------------------------------------------
    @api.depends('value')
    def _compute_state(self):
        for rec in self:
            rec.state = 'translated' if (rec.value or '').strip() else 'to_translate'

    @staticmethod
    def _make_key(term_type, lang, module, model_name, field_name, res_id, src):
        raw = u'|'.join([
            term_type or '', lang or '', module or '', model_name or '',
            field_name or '', str(res_id or 0), src or '',
        ])
        return hashlib.sha1(raw.encode('utf-8')).hexdigest()

    def _key_from_vals(self, vals):
        lang = vals.get('lang')
        if not lang and vals.get('lang_id'):
            lang = self.env['res.lang'].browse(vals['lang_id']).code
        return self._make_key(
            vals.get('term_type'), lang, vals.get('module'),
            vals.get('model_name'), vals.get('field_name'),
            vals.get('res_id'), vals.get('src'))

    # ------------------------------------------------------------------
    # Persistence -> push translations to their real store
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('term_key'):
                vals['term_key'] = self._key_from_vals(vals)
        records = super().create(vals_list)
        if not self.env.context.get('translation_no_push'):
            code_terms = records.filtered(
                lambda r: r.term_type in CODE_TYPES and (r.value or ''))
            if code_terms:
                code_terms.write({'is_override': True})  # triggers _apply_code
        return records

    def write(self, vals):
        res = super().write(vals)
        if self.env.context.get('translation_no_push'):
            return res
        if any(k in vals for k in ('value', 'src', 'lang_id', 'is_override')):
            db_terms = self.filtered(lambda r: r.term_type in DB_TYPES)
            if db_terms and 'value' in vals:
                db_terms._apply_db_translation()
            code_terms = self.filtered(lambda r: r.term_type in CODE_TYPES)
            if code_terms:
                if 'value' in vals:
                    # an edited code value becomes an override
                    to_flag = code_terms.filtered(lambda r: not r.is_override)
                    if to_flag:
                        super(TranslationTerm, to_flag).write({'is_override': True})
                if 'value' in vals or 'is_override' in vals:
                    code_terms._apply_code_translation()
        return res

    def unlink(self):
        had_code = any(r.term_type in CODE_TYPES and r.is_override for r in self)
        env = self.env
        res = super().unlink()
        if had_code:
            ctp.refresh_overrides(env)
            env.registry.clear_cache()
        return res

    def _apply_db_translation(self):
        """Write the value back to the record's translatable field."""
        for rec in self:
            if not (rec.model_name and rec.field_name and rec.res_id and rec.lang):
                continue
            if rec.model_name not in self.env.registry:
                continue
            record = self.env[rec.model_name].sudo().browse(rec.res_id)
            if not record.exists():
                continue
            field = record._fields.get(rec.field_name)
            if not field or not field.translate:
                continue
            try:
                if callable(field.translate):
                    # per-term field: {lang: {source_term: new_term}}
                    record.update_field_translations(
                        rec.field_name, {rec.lang: {rec.src: rec.value or ''}})
                else:
                    # whole-value field: {lang: value} (False clears it)
                    value = rec.value if (rec.value or '') != '' else False
                    record.update_field_translations(
                        rec.field_name, {rec.lang: value})
            except Exception as exc:
                raise UserError(_(
                    "Could not store the translation for %(model)s.%(field)s "
                    "(record %(rid)s): %(err)s",
                    model=rec.model_name, field=rec.field_name,
                    rid=rec.res_id, err=exc))

    def _apply_code_translation(self):
        """Refresh the in-memory code overrides and bust the web cache.

        ``clear_cache`` invalidates the ormcache-backed ``_override_map`` and the
        web-client translation hash in every worker; ``refresh_overrides`` keeps
        the in-memory fallback (used outside requests) current in this worker.
        """
        ctp.refresh_overrides(self.env)
        self.env.registry.clear_cache()

    @api.model
    @tools.ormcache()
    def _override_map(self):
        """{(kind, module, lang): {source: value}} of user code overrides.

        ormcache-backed so request workers share it and a registry cache clear
        (on edit) invalidates it everywhere. Treat the result as read-only.
        """
        return ctp.build_override_map(self.env)

    # ------------------------------------------------------------------
    # Auto-sync on schema change (module install / upgrade / uninstall)
    # ------------------------------------------------------------------
    def _register_hook(self):
        """After every registry load, resync terms when the set of translatable
        fields changed (a module added or removed translatable fields). The
        check is cheap; the heavy reload is deferred to the sync cron so module
        installs/upgrades are never blocked."""
        super()._register_hook()
        try:
            self.env['translation.term']._auto_sync_on_schema_change()
        except Exception:  # never break registry loading
            _logger.exception("translation_manager: auto-sync hook failed")

    @api.model
    def _translatable_fields_fingerprint(self):
        """A hash of every (model, field) that is translatable and stored."""
        parts = []
        for name in self.env.registry.models:
            if name not in self.env:
                continue
            model = self.env[name]
            if model._abstract or model._transient:
                continue
            for fname, field in model._fields.items():
                if field.translate and field.store and getattr(
                        field, 'column_type', None):
                    parts.append(u'%s.%s' % (name, fname))
        parts.sort()
        return hashlib.sha1(u'|'.join(parts).encode('utf-8')).hexdigest()

    @api.model
    def _auto_sync_on_schema_change(self):
        icp = self.env['ir.config_parameter'].sudo()
        fingerprint = self._translatable_fields_fingerprint()
        if icp.get_param(PARAM_FINGERPRINT) == fingerprint:
            return
        cron = self.env.ref(
            'translation_manager.ir_cron_sync_terms', raise_if_not_found=False)
        if not cron:
            # _register_hook can run before our data is loaded on first install;
            # don't store the fingerprint yet so a later call retries.
            return
        # remember this schema so we only resync when it actually changes
        icp.set_param(PARAM_FINGERPRINT, fingerprint)
        # nothing to translate without a second language; the manual refresh or
        # the safety-net cron will populate once one is activated
        if self.env['res.lang'].sudo().search_count(
                [('active', '=', True), ('code', '!=', 'en_US')]) == 0:
            return
        cron._trigger()

    @api.model
    def _cron_sync_terms(self):
        """Upkeep run: drop stale terms, then (re)load everything for all active
        languages. Triggered automatically when translatable fields change, and
        on the cron's own safety-net schedule."""
        langs = self.env['res.lang'].sudo().search(
            [('active', '=', True), ('code', '!=', 'en_US')]).mapped('code')
        if not langs:
            return
        self._prune_stale_terms()
        self.load_terms(lang_codes=langs)

    @api.model
    def _prune_stale_terms(self):
        """Remove terms whose field/model no longer exists or whose module is no
        longer installed (handles uninstall and field removal)."""
        stale = self.browse()
        for rec in self.sudo().search([('term_type', 'in', list(DB_TYPES))]):
            if rec.model_name not in self.env:
                stale |= rec
                continue
            field = self.env[rec.model_name]._fields.get(rec.field_name)
            if not field or not field.translate:
                stale |= rec
        installed = self.env['ir.module.module'].sudo().search(
            [('state', '=', 'installed')]).mapped('name')
        stale |= self.sudo().search(
            [('term_type', 'in', list(CODE_TYPES)),
             ('module', 'not in', list(installed))])
        if stale:
            stale.with_context(translation_no_push=True).sudo().unlink()

    # ------------------------------------------------------------------
    # Loading engine
    # ------------------------------------------------------------------
    @api.model
    def load_terms(self, lang_codes, model_names=None, module_names=None,
                   record_limit=0):
        """Populate ``translation.term`` rows. Returns a counters dict.

        ``model_names`` and ``module_names`` are optional, cross-filling scopes:

        * a **model** loads every record of that model (its field/view terms),
          plus the code terms of the module that owns the model;
        * a **module** loads the terms of every record it owns — field labels,
          menus, views, action names, selections, mail templates, ... resolved
          through ``ir.model.data`` — plus its code terms.

        Empty scopes load everything."""
        lang_codes = [c for c in (lang_codes or []) if c and c != 'en_US']
        if not lang_codes:
            raise UserError(_("Select at least one language other than English (en_US)."))
        targets = self._db_targets(model_names, module_names)
        # code terms come per-module; a chosen model also pulls its owner module
        module_set = set(module_names or [])
        for name in (model_names or []):
            if name in self.env:
                owner = getattr(self.env[name], '_original_module', None)
                if owner:
                    module_set.add(owner)
        counts = {'db': 0, 'code': 0}
        counts['db'] = self._load_db_terms(lang_codes, targets, record_limit)
        counts['code'] = self._load_code_terms(lang_codes, module_set or None)
        return counts

    @api.model
    def _db_targets(self, model_names, module_names):
        """Resolve which records to scan for database terms.

        Returns ``None`` (every model, every record) or a dict
        ``{model_name: None | set(res_ids)}`` where ``None`` means all records of
        that model and a set limits to the specific records a module owns. A
        module's records are found through ``ir.model.data`` so its field labels,
        menus, views and actions — which live on ``base``-owned models — are
        included, not just the models the module itself defines."""
        if not model_names and not module_names:
            return None
        targets = {}
        for name in (model_names or []):
            targets[name] = None  # all records of an explicitly chosen model
        if module_names:
            data = self.env['ir.model.data'].sudo().search(
                [('module', 'in', list(module_names))])
            for d in data:
                if not d.model or not d.res_id:
                    continue
                cur = targets.get(d.model, 'missing')
                if cur is None:
                    continue  # already loading every record of this model
                if cur == 'missing':
                    targets[d.model] = set()
                targets[d.model].add(d.res_id)
        return targets

    def _owner_modules(self, model_names):
        """Map ``(model, res_id) -> module`` from ``ir.model.data`` so each term
        is attributed to the module that owns the record (a sale menu reads as
        ``sale``, not ``base``). Consistent across full and scoped loads."""
        owner = {}
        data = self.env['ir.model.data'].sudo().search(
            [('model', 'in', list(model_names))])
        for d in data:
            if d.res_id:
                owner.setdefault((d.model, d.res_id), d.module)
        return owner

    def _load_db_terms(self, lang_codes, targets, record_limit):
        Term = self.env['translation.term'].with_context(
            translation_no_push=True, active_test=False).sudo()
        lang_recs = self.env['res.lang'].sudo().search(
            [('code', 'in', lang_codes)])
        lang_by_code = {l.code: l.id for l in lang_recs}
        names = (list(targets.keys()) if targets is not None
                 else list(self.env.registry.models.keys()))
        owner_by = self._owner_modules(names)

        created = 0
        buffer = []
        for model_name in names:
            if model_name not in self.env.registry:
                continue
            model = self.env[model_name]
            if model._abstract or model._transient:
                continue
            tfields = [
                f for f in model._fields.values()
                if f.translate and f.store and getattr(f, 'column_type', None)
            ]
            if not tfields:
                continue
            ids = targets.get(model_name) if targets is not None else None
            try:
                base = model.sudo().with_context(
                    active_test=False, prefetch_langs=True)
                if ids is None:
                    records = base.search([])
                    if record_limit:
                        records = records[:record_limit]
                else:
                    records = base.browse(sorted(ids)).exists()
            except Exception:
                _logger.debug("translation_manager: cannot read %s", model_name)
                continue
            default_module = model._original_module if hasattr(
                model, '_original_module') else None
            for record in records:
                term_module = owner_by.get(
                    (model_name, record.id), default_module)
                try:
                    res_name = record.display_name
                except Exception:
                    res_name = "%s,%s" % (model_name, record.id)
                for field in tfields:
                    is_term = callable(field.translate)
                    term_type = 'model_term' if is_term else 'model'
                    try:
                        translations, _ctx = record.get_field_translations(
                            field.name, langs=lang_codes + ['en_US'])
                    except Exception:
                        continue
                    for tr in translations:
                        lang = tr.get('lang')
                        if lang == 'en_US' or lang not in lang_by_code:
                            continue
                        src = tr.get('source')
                        if src in (None, '', False):
                            continue
                        value = tr.get('value') or ''
                        # whole-value fields fall back to en_US when untranslated
                        if not is_term and value == src:
                            value = ''
                        buffer.append({
                            'term_type': term_type,
                            'lang_id': lang_by_code[lang],
                            'module': term_module,
                            'model_name': model_name,
                            'field_name': field.name,
                            'res_id': record.id,
                            'res_name': res_name,
                            'src': src,
                            'value': value,
                        })
                if len(buffer) >= 1000:
                    created += self._upsert_terms(Term, buffer)
                    buffer = []
        created += self._upsert_terms(Term, buffer)
        return created

    def _load_code_terms(self, lang_codes, module_names):
        from odoo.tools.translate import code_translations
        Term = self.env['translation.term'].with_context(
            translation_no_push=True).sudo()
        lang_recs = self.env['res.lang'].sudo().search([('code', 'in', lang_codes)])
        lang_by_code = {l.code: l.id for l in lang_recs}

        if module_names:
            modules = list(module_names)
        else:
            modules = self.env['ir.module.module'].sudo().search(
                [('state', '=', 'installed')]).mapped('name')

        created = 0
        buffer = []
        for module in modules:
            for code in lang_codes:
                lang_id = lang_by_code.get(code)
                if not lang_id:
                    continue
                try:
                    py = code_translations.get_python_translations(module, code)
                except Exception:
                    py = {}
                for src, value in (py or {}).items():
                    buffer.append({
                        'term_type': 'code_python', 'lang_id': lang_id,
                        'module': module, 'src': src, 'value': value or '',
                    })
                try:
                    web = code_translations.get_web_translations(module, code)
                    web_items = {m['id']: m['string'] for m in web.get('messages', ())}
                except Exception:
                    web_items = {}
                for src, value in web_items.items():
                    buffer.append({
                        'term_type': 'code_web', 'lang_id': lang_id,
                        'module': module, 'src': src, 'value': value or '',
                    })
                if len(buffer) >= 1000:
                    created += self._upsert_terms(Term, buffer)
                    buffer = []
        created += self._upsert_terms(Term, buffer)
        return created

    def _upsert_terms(self, Term, vals_list):
        """Idempotent upsert of a batch keyed by ``term_key``."""
        if not vals_list:
            return 0
        for vals in vals_list:
            vals['term_key'] = self._key_from_vals(vals)
        # de-duplicate within the batch (keep last)
        unique = {vals['term_key']: vals for vals in vals_list}
        keys = list(unique.keys())
        existing = Term.search([('term_key', 'in', keys)])
        by_key = {t.term_key: t for t in existing}
        to_create = []
        for key, vals in unique.items():
            term = by_key.get(key)
            if term:
                # refresh source/value display without re-pushing (no_push ctx)
                if term.value != vals.get('value') or term.res_name != vals.get('res_name'):
                    term.write({
                        'value': vals.get('value') or '',
                        'res_name': vals.get('res_name'),
                    })
            else:
                to_create.append(vals)
        if to_create:
            Term.create(to_create)
        return len(to_create)
