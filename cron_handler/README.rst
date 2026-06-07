Cron Handler
==============

Run any Odoo model method on daily, weekly, or monthly schedules using local
time and a configurable timezone — without creating a separate ``ir.cron`` for
each job.

Installation
------------

Install the module from Apps. Assign **Cron Handler / Manager** to users who
should configure handlers (administrators receive this group by default).

Usage
-----

1. Open **Settings → Technical → Cron Handlers**.
2. Create a handler and set:

   * **Target model** — any concrete (non-transient) model.
   * **Method name** — method on that model (default: ``cron_handler_run``).
   * **Timezone** — local timezone for schedule matching (defaults from company/user).

3. Add one or more **schedule lines** (daily / weekly / monthly + hour 0–23).
4. Implement the method on your model, for example::

    from odoo import models

    class MyModel(models.Model):
        _name = 'my.model'

        @api.model
        def cron_handler_run(self):
            handlers = self.env['cron.handler'].search([
                ('model_id.model', '=', 'my.model'),
                ('run_method', '=', 'cron_handler_run'),
                ('is_active', '=', True),
            ])
            ...

Technical notes
---------------

* A scheduled action runs every hour and dispatches matching lines (hour of day only, no minutes).
* ``last_run_at`` prevents double execution within the same local hour slot.
* The module uses the standard library ``zoneinfo`` (no extra Python packages).

Changelog
---------

18.0.1.0.0
~~~~~~~~~~

* Initial public release for Odoo 18.

Credits
-------

**Authors:** TechStars Solution

**License:** LGPL-3
