{
    "name": "Currency Rate Guard",
    "summary": "Block confirmation/posting of purchase orders, vendor bills, "
               "customer invoices and payments when today's currency rate is "
               "missing for guarded currencies. Daily reminder to accountants.",
    "version": "18.0.1.0.0",
    "category": "Accounting/Accounting",
    "license": "LGPL-3",
    "author": "Attefeh Falah",
    "company": "Tech Stars SPC",
    "maintainer": "Tech Stars SPC",
    "website": "https://www.attefehfalah.com",
    "support": "attefehfalah@gmail.com",
    "images": [
        "static/description/cover.png",
        "static/description/screenshot01.png",
        "static/description/screenshot02.png",
        "static/description/screenshot03.png",
    ],
    "depends": ["account", "purchase"],
    "data": [
        "security/ir.model.access.csv",
        "views/res_currency_views.xml",
        "wizard/currency_rate_quick_entry_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
