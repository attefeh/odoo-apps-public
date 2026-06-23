# -*- coding: utf-8 -*-
{
    'name': 'Report Builder (Visual Designer)',
    'version': '19.0.1.0.0',
    'category': 'Technical',
    'summary': 'Design and customize PDF report templates visually — drag, drop, '
               'resize, bind fields/loops/conditions — no code required',
    'description': """
Report Builder
==============

A no-code, drag-and-drop environment to create or customize **PDF report
templates** — without writing QWeb or XML by hand.

Pick a model, drop blocks on a canvas, bind them to record data, and publish:
the builder turns your design into a real Odoo report that prints from the
record's **Print** menu, with the standard company letterhead and paper format.

Features
--------

* **Visual canvas** (powered by the open-source GrapesJS editor, bundled in the
  module — works fully on Odoo Community, no external service):

  * Drag, drop, resize and style blocks: text, headings, images, tables,
    columns and containers.
  * Lossless reopen — your layout is preserved exactly as you left it.

* **Live data binding, no code:**

  * **Fields** — insert any field of the chosen model (and one hop of related
    fields), rendered with Odoo's native formatting.
  * **Loops** — repeat a table row (or any block) over line items
    (e.g. invoice / order lines).
  * **Conditions** — show or hide a block based on a record condition.

* **Real Odoo reports:** publishing creates an ``ir.actions.report`` bound to
  the model, so the report appears in the record's Print menu and renders to
  PDF using the company's external layout and paper format.

* **Safe by design:** expressions run through Odoo's QWeb sandbox (no imports,
  no arbitrary code); designs are validated and test-rendered before publishing.

Usage
-----

#. Open **Report Builder** and click **New** — choose the model and a starter
   layout.
#. Design on the canvas; use the **Field**, **Loop** and **Condition** blocks
   to bind data.
#. Click **Publish**, then **Print Preview** — or print from any record of the
   model.
    """,
    'author': 'Attefeh Falah',
    'company': 'Tech Stars SPC',
    'maintainer': 'Tech Stars SPC',
    'website': 'https://www.attefehfalah.com',
    'support': 'attefehfalah@gmail.com',
    'depends': ['base', 'web'],
    'data': [
        'security/report_builder_security.xml',
        'security/ir.model.access.csv',
        'wizard/report_builder_new_views.xml',
        'views/report_builder_template_views.xml',
        'views/report_builder_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'report_builder/static/lib/grapesjs/grapes.min.css',
            'report_builder/static/lib/grapesjs/grapes.min.js',
            'report_builder/static/src/field_picker.js',
            'report_builder/static/src/blocks_static.js',
            'report_builder/static/src/blocks_dynamic.js',
            'report_builder/static/src/gjs_setup.js',
            'report_builder/static/src/report_builder_action.js',
            'report_builder/static/src/report_builder_action.xml',
            'report_builder/static/src/report_builder_action.scss',
        ],
    },
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
