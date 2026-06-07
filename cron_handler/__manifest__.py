# -*- coding: utf-8 -*-
{
    'name': 'Cron Handler',
    'version': '19.0.1.0.0',
    'category': 'Tools',
    'summary': 'Run scheduled actions at a set time of day (3 PM daily, etc.) instead of fixed intervals',
    'description': """
Cron Handler
============

Native Odoo scheduled actions run on a fixed interval (every N hours/days).
Cron Handler lets you run them at a **specific time of day** instead — for
example 3 PM every day, every Monday, or on the 1st of each month — for any
existing Scheduled Action or any method on any non-transient model.

Features
--------

* Multiple schedule lines per handler — daily, weekly, or monthly at a chosen
  local hour (per-handler timezone)
* Link an existing **Scheduled Action**: while the handler is active that
  action is **automatically deactivated** so it no longer runs on its own
  interval, and it is run only at your scheduled times (no conflict). Clearing
  the link or deactivating the handler restores the action.
* Or target any non-transient model + method directly
* Company-aware configuration
* Duplicate-run protection within the same local hour slot
* Dedicated security groups (User / Manager)

Configuration
-------------

#. Install the module and assign **Cron Handler / Manager** to administrators.
#. Go to **Settings → Technical → Cron Handlers**.
#. Create a handler: choose target model, method name, and timezone.
#. Add schedule lines with frequency and hour of day (0–23).
#. Implement the target method on your model (see README).

The dispatcher runs every hour via a built-in scheduled action.
    """,
    'author': 'Attefeh Falah',
    'company': 'Tech Stars SPC',
    'maintainer': 'Tech Stars SPC',
    'website': 'https://www.attefehfalah.com',
    'support': 'attefehfalah@gmail.com',
    'depends': ['base'],
    'images': [
        'static/description/cover.png',
    ],
    'data': [
        'security/cron_handler_security.xml',
        'security/ir.model.access.csv',
        'views/cron_handler_views.xml',
        'data/cron.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
