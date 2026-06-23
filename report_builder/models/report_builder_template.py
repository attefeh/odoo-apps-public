# -*- coding: utf-8 -*-
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .report_builder_compiler import compile_body_to_arch, ReportCompileError

_logger = logging.getLogger(__name__)

# Fields never worth offering in the visual field picker.
_SKIP_FIELDS = {'__last_update', 'display_name', 'create_uid', 'write_uid',
                'create_date', 'write_date'}


class ReportBuilderTemplate(models.Model):
    _name = 'report.builder.template'
    _description = 'Report Builder Template'
    _order = 'name'

    name = fields.Char(required=True)
    model_id = fields.Many2one(
        'ir.model', string='Model', required=True, ondelete='cascade',
        help="The record type this report runs on.")
    model_name = fields.Char(related='model_id.model', store=True, readonly=True,
                             string='Model (technical)')
    layout = fields.Selection(
        [('external', 'Company letterhead (external layout)'),
         ('internal', 'Minimal header (internal layout)'),
         ('blank', 'Blank (no header/footer)')],
        string='Layout', default='external', required=True)
    paperformat_id = fields.Many2one(
        'report.paperformat', string='Paper Format',
        help="Leave empty to use the company default paper format.")

    body_html = fields.Text(string='Design HTML', default='')
    gjs_data = fields.Text(string='Editor State')

    view_id = fields.Many2one('ir.ui.view', string='Generated View',
                              readonly=True, ondelete='set null', copy=False)
    report_id = fields.Many2one('ir.actions.report', string='Generated Report',
                                readonly=True, ondelete='set null', copy=False)
    compiled_arch = fields.Text(string='Compiled Arch', readonly=True, copy=False)
    error_message = fields.Text(string='Last Error', readonly=True, copy=False)

    state = fields.Selection(
        [('draft', 'Draft'), ('published', 'Published')],
        default='draft', required=True, copy=False)
    add_print_binding = fields.Boolean(
        string='Show in Print menu', default=True,
        help="Add the report to the record's Print menu when published.")
    group_ids = fields.Many2many(
        'res.groups', string='Restrict to Groups',
        help="Optional: only these groups can use the published report.")
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company)

    # ------------------------------------------------------------------
    # Key / identity
    # ------------------------------------------------------------------
    def _report_key(self):
        self.ensure_one()
        return 'report_builder.tpl_%d' % self.id

    # ------------------------------------------------------------------
    # Editor entry point + save round-trip
    # ------------------------------------------------------------------
    def action_open_editor(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'report_builder.editor',
            'target': 'fullscreen',
            'name': _("Report Builder — %s", self.name),
            'context': {'template_id': self.id},
        }

    @api.model
    def save_design(self, template_id, body_html, gjs_data):
        """Persist the editor's HTML + project state (called from OWL)."""
        tmpl = self.browse(template_id)
        tmpl.write({'body_html': body_html or '', 'gjs_data': gjs_data or ''})
        return True

    @api.model
    def load_editor_data(self, template_id):
        """Return everything the editor needs to boot."""
        tmpl = self.browse(template_id)
        tmpl.ensure_one()
        return {
            'id': tmpl.id,
            'name': tmpl.name,
            'model': tmpl.model_name,
            'model_label': tmpl.model_id.name,
            'body_html': tmpl.body_html or '',
            'gjs_data': tmpl.gjs_data or '',
            'state': tmpl.state,
            'fields': self.get_model_fields(tmpl.model_name),
        }

    # ------------------------------------------------------------------
    # Field picker data source
    # ------------------------------------------------------------------
    @api.model
    def get_model_fields(self, model_name):
        """Return a JSON-able description of ``model_name``'s usable fields."""
        if not model_name or model_name not in self.env:
            return []
        result = []
        for fname, meta in self.env[model_name].fields_get().items():
            if fname in _SKIP_FIELDS:
                continue
            ttype = meta.get('type')
            if ttype == 'binary' and meta.get('name') != 'image':
                # keep image-ish binaries, skip raw blobs
                if 'image' not in fname and 'logo' not in fname:
                    continue
            result.append({
                'name': fname,
                'string': meta.get('string') or fname,
                'type': ttype,
                'relation': meta.get('relation') or False,
                'is_relational': bool(meta.get('relation')),
                'is_x2many': ttype in ('one2many', 'many2many'),
                'translate': bool(meta.get('translate')),
            })
        result.sort(key=lambda f: (not f['is_x2many'], f['string'].lower()))
        return result

    # ------------------------------------------------------------------
    # Publish / unpublish
    # ------------------------------------------------------------------
    def action_publish(self):
        self.ensure_one()
        if not self.model_name:
            raise UserError(_("Pick a model before publishing."))
        try:
            arch = compile_body_to_arch(self.body_html, self.layout, self._report_key())
        except ReportCompileError as exc:
            self.error_message = str(exc)
            raise UserError(_("This design can't be published yet.\n\n%s", exc))

        key = self._report_key()
        # 1. Upsert the QWeb view.
        view_vals = {'name': self.name, 'type': 'qweb', 'arch': arch, 'key': key}
        if self.view_id:
            self.view_id.write({'arch': arch, 'name': self.name})
        else:
            self.view_id = self.env['ir.ui.view'].create(view_vals)

        # 2. Upsert the report action.
        report_vals = {
            'name': self.name,
            'model': self.model_name,
            'report_type': 'qweb-pdf',
            'report_name': key,
            'paperformat_id': self.paperformat_id.id or False,
            'group_ids': [(6, 0, self.group_ids.ids)],
        }
        if self.report_id:
            self.report_id.write(report_vals)
        else:
            self.report_id = self.env['ir.actions.report'].create(report_vals)

        # 3. Print-menu binding.
        if self.add_print_binding:
            self.report_id.write({'binding_model_id': self.model_id.id,
                                   'binding_type': 'report'})
        else:
            self.report_id.write({'binding_model_id': False})

        # 4. Sample pre-render to catch bad expressions before going live.
        self._sample_render()

        self.write({'state': 'published', 'compiled_arch': arch,
                    'error_message': False})
        return self._notify(_("Report published."))

    def _sample_render(self):
        """Render the report against one real record; raise a friendly error."""
        self.ensure_one()
        rec = self.env[self.model_name].search([], limit=1)
        if not rec:
            return  # nothing to render against yet; allow publish
        try:
            self.report_id._render_qweb_html(self.report_id.id, rec.ids)
        except UserError:
            raise
        except Exception as exc:
            self.error_message = str(exc)
            raise UserError(_(
                "The report was generated but failed to render with real data. "
                "Check your field names and expressions.\n\n%s", exc))

    def action_unpublish(self):
        self.ensure_one()
        if self.report_id:
            self.report_id.write({'binding_model_id': False})
        self.state = 'draft'
        return self._notify(_("Report removed from the Print menu."))

    def action_print_preview(self):
        self.ensure_one()
        if self.state != 'published' or not self.report_id:
            raise UserError(_("Publish the report before previewing it."))
        rec = self.env[self.model_name].search([], limit=1)
        if not rec:
            raise UserError(_("There is no %s record to preview with.",
                              self.model_id.name))
        return self.report_id.report_action(rec)

    def _notify(self, message):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {'message': message, 'type': 'success', 'sticky': False},
        }

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------
    def unlink(self):
        reports = self.report_id
        views = self.view_id
        res = super().unlink()
        for rec in reports:
            try:
                rec.unlink()
            except Exception:
                _logger.debug("report_builder: could not remove report %s", rec.id)
        for rec in views:
            try:
                rec.unlink()
            except Exception:
                _logger.debug("report_builder: could not remove view %s", rec.id)
        return res
