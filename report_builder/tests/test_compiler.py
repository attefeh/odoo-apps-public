# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

from ..models.report_builder_compiler import compile_body_to_arch, ReportCompileError


@tagged("post_install", "-at_install")
class TestReportBuilder(TransactionCase):

    def _make_template(self, body, model="res.company"):
        model_id = self.env["ir.model"]._get(model)
        return self.env["report.builder.template"].create({
            "name": "Test Report",
            "model_id": model_id.id,
            "layout": "external",
            "body_html": body,
        })

    # -- pure compiler -----------------------------------------------------
    def test_compile_field_loop_condition(self):
        body = (
            '<div>'
            '<h1 data-rb-field="doc.name" data-rb-out="field">X</h1>'
            '<div data-rb-if="doc.partner_id"><span>has partner</span></div>'
            '<table><tr data-rb-foreach="doc.child_ids" data-rb-as="child" '
            'data-rb-if="child.active"><td data-rb-field="child.name">y</td></tr></table>'
            '<span data-rb-field="doc.id * 2" data-rb-out="out">0</span>'
            '</div>'
        )
        arch = compile_body_to_arch(body, "external", "report_builder.tpl_1")
        self.assertIn('t-field="doc.name"', arch)
        self.assertIn('t-if="doc.partner_id"', arch)
        self.assertIn('t-foreach="doc.child_ids"', arch)
        self.assertIn('t-as="child"', arch)
        self.assertIn('t-key="child_index"', arch)
        self.assertIn('t-if="child.active"', arch)        # stays on the loop node
        self.assertIn('t-out="doc.id * 2"', arch)          # expression -> t-out
        self.assertIn('t-call="web.external_layout"', arch)

    def test_compile_rejects_loop_without_alias(self):
        with self.assertRaises(ReportCompileError):
            compile_body_to_arch(
                '<div data-rb-foreach="doc.child_ids"></div>', "blank", "k")

    # -- full publish + render --------------------------------------------
    def test_publish_and_render(self):
        company = self.env.company
        body = (
            '<div>'
            '<h1 data-rb-field="doc.name" data-rb-out="field">name</h1>'
            '<ul><li data-rb-foreach="doc.child_ids" data-rb-as="child">'
            '<span data-rb-field="child.name">child</span></li></ul>'
            '</div>'
        )
        tmpl = self._make_template(body)
        tmpl.action_publish()
        self.assertEqual(tmpl.state, "published")
        self.assertTrue(tmpl.view_id)
        self.assertEqual(tmpl.view_id.key, tmpl.report_id.report_name)
        self.assertEqual(tmpl.report_id.binding_model_id.model, "res.company")

        html, _dummy = tmpl.report_id._render_qweb_html(tmpl.report_id.id, company.ids)
        html = html.decode() if isinstance(html, bytes) else html
        self.assertIn(company.name, html)
        for child in company.child_ids:
            self.assertIn(child.name, html)

    def test_publish_bad_field_raises(self):
        tmpl = self._make_template(
            '<span data-rb-field="doc.this_field_does_not_exist" data-rb-out="field">x</span>'
        )
        with self.assertRaises(UserError):
            tmpl.action_publish()

    def test_unlink_cleans_up(self):
        tmpl = self._make_template(
            '<span data-rb-field="doc.name" data-rb-out="field">x</span>'
        )
        tmpl.action_publish()
        view = tmpl.view_id
        report = tmpl.report_id
        tmpl.unlink()
        self.assertFalse(view.exists())
        self.assertFalse(report.exists())
