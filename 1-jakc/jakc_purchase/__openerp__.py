# -*- coding: utf-8 -*-

{
    'name': 'Jakc Labs - Purchase Enhancement',
    'version': '9.0.0.1.0',
    'category': 'General',
    'license': 'AGPL-3',
    'summary': 'Purchase Enchancement',
    'author': "Jakc Labs",
    'website': 'http://www.jakc-labs.com/',
    'depends': [
        'purchase',
        'jakc_sale',
    ],
    'data': [
        'views/jakc_purchase_view.xml',
        'report/purchase_order_report.xml',
        'report/report_purchaseorder.xml'
    ],
    'installable': True,
    'application': True,
}
