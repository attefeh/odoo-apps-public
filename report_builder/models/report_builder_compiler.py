# -*- coding: utf-8 -*-
"""HTML (GrapesJS) -> QWeb arch compiler.

The visual editor emits plain HTML annotated with ``data-rb-*`` attributes that
describe the dynamic parts of the report.  This module turns that HTML into a
well-formed QWeb template arch (a string) ready to be stored on an
``ir.ui.view`` of type ``qweb``.

The transformation is purely structural; it never evaluates user expressions.
Expressions are emitted verbatim into QWeb directives and are evaluated later by
Odoo's QWeb engine, which runs them through its safe_eval opcode whitelist (no
imports, no attribute assignment).  The worst a bad expression can do is raise a
render-time error, which the model catches with a sample pre-render at publish.
"""
import re

import lxml.html
from lxml import etree

# Editor-only attributes that must never reach the stored arch. Classes and ids
# are kept on purpose: the editor's style rules (injected as <style>) target them.
_DROP_ATTRS = ('contenteditable', 'draggable', 'spellcheck')
_FIELD_PATH_RE = re.compile(r'^[A-Za-z_][\w]*(\.[A-Za-z_][\w]*)+$')


class ReportCompileError(Exception):
    """Raised when a design cannot be compiled into a valid QWeb arch."""


def _is_field_path(expr):
    return bool(_FIELD_PATH_RE.match((expr or '').strip()))


def _translate_element(el):
    """Translate one element's ``data-rb-*`` attributes into QWeb directives."""
    foreach = el.get('data-rb-foreach')
    as_ = el.get('data-rb-as')
    if_ = el.get('data-rb-if')
    field = el.get('data-rb-field')
    out_mode = (el.get('data-rb-out') or '').strip()

    # data-rb-att-NAME -> t-att-NAME (dynamic attributes such as src/href)
    for attr in list(el.attrib):
        if attr.startswith('data-rb-att-'):
            name = attr[len('data-rb-att-'):]
            if name:
                el.set('t-att-%s' % name, el.get(attr))
            del el.attrib[attr]

    if foreach:
        if not as_:
            raise ReportCompileError(
                "A repeated block is missing its loop variable name "
                "(set 'Repeat as' on the Loop block).")
        el.set('t-foreach', foreach)
        el.set('t-as', as_)
        el.set('t-key', '%s_index' % as_)
    if if_:
        # QWeb evaluates foreach before if on the same node, so a t-if that
        # references the loop alias is correctly scoped per iteration.
        el.set('t-if', if_)
    if field:
        # t-field needs a real dotted field path; expressions use t-out.
        use_field = (out_mode == 'field') or (out_mode != 'out' and _is_field_path(field))
        if use_field and _is_field_path(field):
            el.set('t-field', field)
        else:
            el.set('t-out', field)
        # QWeb replaces the element's content, so drop the editor placeholder.
        for child in list(el):
            el.remove(child)
        el.text = None

    # Strip the source data-rb-* attributes and editor cruft (keep class/id/style).
    for attr in list(el.attrib):
        if attr.startswith('data-rb-') or attr.startswith('data-gjs') or \
                attr in _DROP_ATTRS:
            del el.attrib[attr]


def _transform(fragment):
    """Walk the parsed fragment, returning the transformed children as XML."""
    for el in list(fragment.iter()):
        if not isinstance(el.tag, str):       # comments / PIs
            continue
        _translate_element(el)
    return ''.join(
        etree.tostring(child, encoding='unicode', method='xml')
        for child in fragment
    )


def compile_body_to_arch(body_html, layout, key):
    """Compile editor HTML into a QWeb arch string.

    :param body_html: HTML produced by the visual editor (may be empty).
    :param layout: 'external', 'internal' or 'blank'.
    :param key: the template key / report_name (e.g. 'report_builder.tpl_5').
    :raises ReportCompileError: if the result is not well-formed XML.
    """
    body_html = (body_html or '').strip()
    try:
        fragment = lxml.html.fragment_fromstring(body_html, create_parent='div')
    except (etree.ParserError, etree.XMLSyntaxError) as exc:
        raise ReportCompileError("The design could not be parsed: %s" % exc)

    body_inner = _transform(fragment)
    arch = _wrap_arch(body_inner, layout, key)

    # Final strict well-formedness check (QWeb requires valid XML).
    try:
        etree.fromstring(arch)
    except etree.XMLSyntaxError as exc:
        raise ReportCompileError(
            "The report layout produced invalid markup (%s). This usually means "
            "a field expression contains an unescaped '<', '>' or '&'." % exc)
    return arch


def _wrap_arch(body_inner, layout, key):
    page = '<div class="page">%s</div>' % body_inner
    if layout == 'blank':
        inner = page
    else:
        external = 'web.internal_layout' if layout == 'internal' else 'web.external_layout'
        inner = '<t t-call="%s">%s</t>' % (external, page)
    return (
        '<t t-name="%(key)s">'
        '<t t-call="web.html_container">'
        '<t t-foreach="docs" t-as="doc">'
        '%(inner)s'
        '</t></t></t>'
    ) % {'key': key, 'inner': inner}
