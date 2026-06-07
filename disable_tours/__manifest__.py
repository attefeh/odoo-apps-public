{
    "name": "Disable Tours",
    "summary": "Permanently disable all Odoo onboarding tours for every user, "
               "across backend and frontend.",
    "description": """
Disable Tours
=============

Odoo's onboarding tours (the floating green helper that walks users through
features the first time they open an app) are killed from both ends:

* Server-side: `ir.http.session_info` always reports `tour_enabled = False`
  and `current_tour = False`, so the JS tour service never tries to resume
  any tour at page load. `res.users.switch_tour_enabled` is overridden to
  refuse re-enabling, so the developer-tools toggle becomes a no-op.

* Client-side: the `tour_service` service registration is replaced with a
  no-op implementation, so even a direct `odoo.startTour(...)` call from
  the console or a URL parameter does nothing.

There is no setting; once installed, tours stay off.
    """,
    "version": "19.0.1.0.1",
    "category": "Tools",
    "license": "LGPL-3",
    "author": "Attefeh Falah",
    "company": "Tech Stars SPC",
    "maintainer": "Tech Stars SPC",
    "website": "https://www.attefehfalah.com",
    "support": "attefehfalah@gmail.com",
    "images": [
        "static/description/cover.png",
    ],
    "depends": ["web_tour"],
    "data": [],
    "assets": {
        "web.assets_backend": [
            "disable_tours/static/src/js/disable_tours.js",
        ],
        "web.assets_frontend": [
            "disable_tours/static/src/js/disable_tours.js",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
