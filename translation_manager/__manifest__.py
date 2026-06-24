# -*- coding: utf-8 -*-
{
    'name': 'Translation Manager (Translated Terms)',
    'version': '19.0.1.0.0',
    'category': 'Technical',
    'summary': 'Bring back the Translated Terms list: edit field, view, menu, '
               'action and code (errors/buttons/JS) translations for every language',
    'description': """
Translation Manager
===================

Older Odoo versions shipped a **Translated Terms** tree under
*Settings > Translations* where you could see and edit every translatable term
of every installed module, one row per language. Odoo 16+ removed that screen
(translations moved to per-record JSONB columns and to module ``.po`` files).

This module brings that workflow back.

What you can translate
-----------------------

* **Database terms** stored per record (fully supported, edits persist normally):

  * Model fields marked ``translate=True`` (product names, descriptions, ...).
  * Per-term fields (view architectures, HTML/Qweb) — every button label,
    menu entry and static text inside a view.
  * Menu names, window-action names, selection labels, email templates, etc.

* **Code terms** extracted from the module source code:

  * Server-side Python messages (``_()`` / ``_lt()`` errors, warnings).
  * Web / JavaScript strings (``_t()`` buttons, client notifications) and
    static QWeb templates.

  Every code term is collected, whether already translated or not, so you can
  translate from scratch. Code edits are applied through a translation-loading
  override, so they take effect without touching the module source.

How it works
------------

#. Open **Settings > Translations > Translated Terms**.
#. Use **Refresh Terms** to load them. Scope it by module, model and language
   (all optional — leave empty to load everything). Loading is manual: it runs
   only when you ask for it.
#. Edit the **Translation** column inline. Database edits are written straight
   back to the record; code edits are stored as overrides and served to both
   the server and the web client.

Notes
-----

* Loading *everything* on a large database can be heavy — scope **Refresh
  Terms** by module, model or language for day-to-day work.
* Code terms are read straight from the source, so untranslated strings show up
  too. You can also add a code override manually (New) when you know
  the exact source string of an error or button.
    """,
    'author': 'Attefeh Falah',
    'company': 'Tech Stars SPC',
    'maintainer': 'Tech Stars SPC',
    'website': 'https://www.attefehfalah.com',
    'support': 'attefehfalah@gmail.com',
    'depends': ['base', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/translation_loader_views.xml',
        'views/translation_term_views.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
