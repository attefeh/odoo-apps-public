{
    "name": "Purchase Order Multiple Print",
    "summary": "Print a purchase order multiple times in one go via a header "
               "button that asks how many copies you need.",
    "version": "18.0.1.0.0",
    "category": "Purchases",
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
    "depends": ["purchase"],
    "data": [
        "security/ir.model.access.csv",
        "wizard/purchase_multiple_print_wizard_views.xml",
        "views/purchase_order_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
