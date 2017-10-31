# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'Financial Report XLS',
    'version' : '1.0',
    'license': 'AGPL-3',
    'summary': 'Financial Report',
    'sequence': 1,
    "author": "Alphasoft",
    'description': """
This module is aim to add balance sheet & profit loss xls
    """,
    'category' : 'Accounting',
    'website': 'https://www.alphasoft.co.id/',
    'images' : ['static/description/main_screenshot.png'],
    'depends' : ['account','jakc_report_xls'],
    'data': [
        'wizard/account_financial_report_view.xml',
        'views/account_view.xml',
    ],
    'demo': [
        
    ],
    'qweb': [
        
    ],
    'price': 75.00,
    'currency': 'EUR',
    'installable': True,
    'auto_install': False,
}
