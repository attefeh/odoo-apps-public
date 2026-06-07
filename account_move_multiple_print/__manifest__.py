{
    "name": "Account Move Multiple Print",
    "summary": "Print an invoice / bill / journal entry multiple times in one "
               "go via a header button that asks how many copies you need.",
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
    ],
    "depends": ["account"],
    "data": [
        "security/ir.model.access.csv",
        "wizard/account_move_multiple_print_wizard_views.xml",
        "views/account_move_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
