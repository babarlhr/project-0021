# -*- coding: utf-8 -*-
#################################################################################
#
#    Copyright (c) 2016-Present Jakc Labs. (<http://www.jakc-labs.com/>)
#
#################################################################################
{
    'name': 'Jakc Labs - POS Enhancement',
    'summary': 'POS Enhancement',
    'version': '1.0',
    'category': 'Point Of Sale',
    "sequence": 1,
    'description': """
Point Of Sale - POS Enhancement
================================

Features:
----------------
    * Add ability to using Credit Card for Payment in POS.
    * For Odoo 9

""",
    "author": "Jakc Labs.",
    'website': 'http://www.jakc-labs.com',
    'depends': [
        'point_of_sale',
        ],
    'data': [
        'views/report_detailsofsales.xml'
    ],
    'qweb': [
        'static/src/xml/pos.xml',
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}