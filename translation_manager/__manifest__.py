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

* **Code terms** that come from the modules' ``.po`` files:

  * Server-side Python messages (``_()`` errors, warnings).
  * Web / JavaScript strings (``_t()`` buttons, client notifications).

  Code terms are applied through a translation-loading override, so your edits
  take effect without touching the module source.

How it works
------------

#. Open **Settings > Translations > Translated Terms**.
#. The list is kept in sync automatically: whenever a module is installed,
   upgraded or uninstalled, the set of translatable terms is refreshed in the
   background (a light weekly cron also picks up new data records).
#. Need an immediate refresh? Use **Refresh Terms** and optionally scope it by
   module, model and language (all optional — leave empty to load everything).
#. Edit the **Translation** column inline. Database edits are written straight
   back to the record; code edits are stored as overrides and served to both
   the server and the web client.

Notes
-----

* Loading *everything* on a large database can be heavy — scope **Refresh
  Terms** by module, model or language for day-to-day work.
* For code terms, the list shows terms that already exist in the installed
  ``.po`` files. You can also add a code override manually (New) when you know
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
        'data/translation_cron.xml',
        'wizard/translation_loader_views.xml',
        'views/translation_term_views.xml',
    ],
    'license': 'LGPL-3',
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': True,
    'auto_install': False,
}
