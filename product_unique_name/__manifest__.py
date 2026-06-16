{
    "name": "Product Unique Name",
    "summary": "Prevent duplicate product and variant names — block creating "
               "or renaming a product or variant to a name that already "
               "exists.",
    "description": """
Product Unique Name
===================

Stops two products (or two variants) from ending up with the same name.

* On every create and rename of a **product**, the name is checked against all
  existing products. Duplicates are rejected with a clear error.
* On every create and rename of a **variant**, the full variant name (the
  product name plus its attribute values, e.g. ``T-Shirt (Red, L)``) is checked
  so legitimate variants are kept while real duplicates are blocked.

Matching is case-insensitive and ignores leading/trailing spaces, so "Desk",
"desk" and " Desk " all count as the same name. In a multi-company database a
name may still be reused across companies; it only clashes within the same
company or against a shared (no-company) record.

There is no setting; once installed, uniqueness is enforced everywhere products
are created — the interface, imports and other apps alike.
    """,
    "version": "18.0.1.0.0",
    "category": "Inventory/Inventory",
    "license": "LGPL-3",
    "author": "Attefeh Falah",
    "company": "Tech Stars SPC",
    "maintainer": "Tech Stars SPC",
    "website": "https://www.attefehfalah.com",
    "support": "attefehfalah@gmail.com",
    "images": [
        "static/description/cover.png",
    ],
    "depends": ["product"],
    "data": [],
    "installable": True,
    "application": False,
    "auto_install": False,
}
