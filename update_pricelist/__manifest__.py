# -*- coding: utf-8 -*-
{
    'name': 'Update Pricelist',
    'version': '18.0.1.0.0',
    'category': 'Sales',
    'summary': 'Bulk update pricelist prices by a fixed amount or a percentage',
    'description': """
Update Pricelist
================

Update the prices of many products on a pricelist at once, either by a fixed
amount or by a percentage of their current price — without editing each
pricelist line by hand.

Features
--------

* **Bulk update wizard** launched from three places:

  * Product Variants list (selected variants)
  * Product Templates list (all their variants)
  * Pricelist Items list (selected lines, one pricelist at a time)

* Increase prices by a **fixed amount** or a **percentage** of the current price.
* Creates new, time-stamped pricelist lines (per-variant rules) and can
  optionally **close the previous open lines** so history is preserved.
* Warns before submitting when selected products have **no current price** on
  the pricelist (a percentage increase would be computed from a base of 0).

Pricelist Items overview
------------------------

A dedicated **Sales → Pricelist Lines** view shows each pricelist line with its
**latest purchase price** (from posted vendor bills), **supplier**, computed
**profit percentage**, and validity dates — with search, filtering on current
prices, and grouping by pricelist.

Usage
-----

#. Open **Sales → Products → Product Variants** (or Pricelist Lines).
#. Select the products/lines to update and click **Update Pricelist**.
#. Choose the pricelist, the update type (Fixed / Percentage) and the amount.
#. Tick **Close Old Pricelists** to end-date the previous lines, then **Submit**.
    """,
    'author': 'Attefeh Falah',
    'company': 'Tech Stars SPC',
    'maintainer': 'Tech Stars SPC',
    'website': 'https://www.attefehfalah.com',
    'support': 'attefehfalah@gmail.com',
    'depends': ['sale_management', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/update_pricelist_item_views.xml',
        'views/product_pricelist_views.xml',
        'views/product_product_views.xml',
    ],
    'images': [
        'static/description/cover.png',
        'static/description/screenshot_wizard.png',
        'static/description/screenshot_pricelist_items.png',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
