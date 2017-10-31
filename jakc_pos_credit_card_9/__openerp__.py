# -*- coding: utf-8 -*-
#################################################################################
#
#    Copyright (c) 2016-Present Jakc Labs. (<http://www.jakc-labs.com/>)
#
#################################################################################
{
    'name': 'POS: Credit Card Payment',
    'summary': 'Extend Payment Features with Credit Card Method',
    'version': '1.0',
    'category': 'Point Of Sale',
    "sequence": 1,
    'description': """
Point Of Sale - Credit Card Payment
=====================================

Features:
----------------
    * Add ability to using Credit Card for Payment in POS.
    * For Odoo 9

""",
    "author": "Wahyu Hidayat - Jakc Labs.",
    'website': 'http://www.jakc-labs.com',
    'depends': [
        'point_of_sale',
        ],
    'data': [
        'views/jakc_pos_credit_card_view.xml',
        'views/templates.xml',
    ],
    'qweb': [
        'static/src/xml/pos_credit_card.xml',
    ],    
    "installable": True,
    "application": True,
    "auto_install": False,        
}