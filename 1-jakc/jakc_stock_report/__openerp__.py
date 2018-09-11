# -*- coding: utf-8 -*-

{
    'name': 'Jakc Labs - Stock Enhancement',
    'version': '9.0.0.1.0',
    'category': 'Stock',
    'license': 'AGPL-3',
    'summary': 'Stock Enchancement',
    'author': "Jakc Labs",
    'website': 'http://www.jakc-labs.com/',
    'depends': [
        'purchase'
    ],
    'data': [
        'views/jakc_stock_scheduler.xml',
        'views/jakc_stock_view.xml',
        'views/jakc_res_users_view.xml',
        'report/report_deliveryslip.xml',
        'report/stock_report.xml'

    ],
    'installable': True,
    'application': True,
}
