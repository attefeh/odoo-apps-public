{
    "name": "Sale Order Multiple Print",
    "summary": "Print a sale order multiple times in one go via a header button "
               "that asks how many copies you need.",
    "version": "19.0.1.0.0",
    "category": "Sales/Sales",
    "license": "LGPL-3",
    "author": "Attefeh Falah",
    "company": "Tech Stars SPC",
    "maintainer": "Tech Stars SPC",
    "website": "https://www.attefehfalah.com",
    "support": "attefehfalah@gmail.com",
    "depends": ["sale"],
    "data": [
        "security/ir.model.access.csv",
        "wizard/sale_multiple_print_wizard_views.xml",
        "views/sale_order_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
