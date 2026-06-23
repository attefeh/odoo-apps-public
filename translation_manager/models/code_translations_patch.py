# -*- coding: utf-8 -*-
"""Per-database override of *code* translations.

Odoo loads code translations (Python ``_()`` messages and web/JS ``_t()``
strings) from each module's ``.po`` files into a process-wide singleton
``odoo.tools.translate.code_translations``.  There is no per-database editing of
those terms anymore.

This module lets users override them from the ``translation.term`` table.  We
wrap the two read methods of ``CodeTranslations`` so that, for the current
database, user overrides are merged on top of the file-based translations.

Both the server ``_()`` path (``get_translation`` ->
``get_python_translations``) and the web client payload
(``ir.http._get_translations_for_webclient`` -> ``get_web_translations``) go
through these two methods, so a single patch covers every code term.

To keep the hot path cheap, overrides are held in an in-memory map keyed by
database name and refreshed only when ``translation.term`` rows change.
"""
import logging
import threading

from odoo.tools import translate as _translate_mod

_logger = logging.getLogger(__name__)

# {db_name: {('python'|'web', module, lang): {source: value}}}
_OVERRIDES = {}
# Databases whose overrides have been loaded at least once (even if empty).
_LOADED = set()
# Guard against re-entrancy while lazily opening a cursor.
_LOADING = set()

_PATCHED = False


def _current_db():
    """Best-effort lookup of the database for the running request/worker."""
    try:
        from odoo.http import request
        if request is not None and getattr(request, 'db', None):
            return request.db
    except Exception:  # pragma: no cover - request may be unavailable
        pass
    return getattr(threading.current_thread(), 'dbname', None)


def build_override_map(env):
    """Read the user overrides for ``env``'s database into a plain dict."""
    data = {}
    Term = env['translation.term'].sudo()
    rows = Term.search([
        ('is_override', '=', True),
        ('term_type', 'in', ('code_python', 'code_web')),
        ('value', '!=', False),
    ])
    for row in rows:
        if not row.src:
            continue
        kind = 'python' if row.term_type == 'code_python' else 'web'
        data.setdefault((kind, row.module or '', row.lang or ''), {})[row.src] = row.value
    return data


def refresh_overrides(env):
    """Rebuild the override map for ``env``'s database (called after edits)."""
    db = env.cr.dbname
    _OVERRIDES[db] = build_override_map(env)
    _LOADED.add(db)
    return _OVERRIDES[db]


def _lazy_load(db):
    """Load overrides for ``db`` once, opening a short-lived cursor."""
    if db in _LOADING:
        return None
    _LOADING.add(db)
    try:
        import odoo
        registry = odoo.registry(db)
        if not registry.ready:
            return None
        if 'translation.term' not in registry:
            _OVERRIDES[db] = {}
            _LOADED.add(db)
            return _OVERRIDES[db]
        with registry.cursor() as cr:
            env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
            return refresh_overrides(env)
    except Exception:  # pragma: no cover - never break translation lookups
        _logger.debug("translation_manager: could not load overrides for %s",
                      db, exc_info=True)
        return None
    finally:
        _LOADING.discard(db)


def _get_override(kind, module, lang):
    key = (kind, module or '', lang or '')
    # 1) Inside a request we have an env: read the ormcache-backed map, which is
    #    invalidated across all workers when an edit clears the registry cache.
    try:
        from odoo.http import request
        if request is not None and getattr(request, 'env', None) is not None:
            return request.env['translation.term'].sudo()._override_map().get(key)
    except Exception:  # pragma: no cover - fall through to the in-memory map
        pass
    # 2) Outside a request (cron, tests): best-effort in-memory map for this db.
    db = _current_db()
    if not db:
        return None
    if db not in _LOADED and _lazy_load(db) is None:
        return None
    data = _OVERRIDES.get(db) or {}
    return data.get(key)


def install_patch():
    """Wrap ``CodeTranslations`` read methods (idempotent)."""
    global _PATCHED
    if _PATCHED:
        return

    CT = _translate_mod.CodeTranslations
    _orig_py = CT.get_python_translations
    _orig_web = CT.get_web_translations

    def get_python_translations(self, module_name, lang):
        res = _orig_py(self, module_name, lang)
        if lang and lang != 'en_US':
            override = _get_override('python', module_name, lang)
            if override:
                merged = dict(res)
                merged.update(override)
                return merged
        return res

    def get_web_translations(self, module_name, lang):
        res = _orig_web(self, module_name, lang)
        if lang and lang != 'en_US':
            override = _get_override('web', module_name, lang)
            if override:
                messages = list(res.get('messages', ()))
                index = {m['id']: i for i, m in enumerate(messages)}
                for src, value in override.items():
                    entry = {'id': src, 'string': value}
                    if src in index:
                        messages[index[src]] = entry
                    else:
                        messages.append(entry)
                return {'messages': tuple(messages)}
        return res

    CT.get_python_translations = get_python_translations
    CT.get_web_translations = get_web_translations
    _PATCHED = True
    _logger.info("translation_manager: code-translation override installed")
