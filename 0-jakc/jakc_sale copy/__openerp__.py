# -*- coding: utf-8 -*-

{
    'name': 'Jakc Labs - Workshop Work Order',
    'version': '9.0.0.1.0',
    'category': 'Workshop',
    'license': 'AGPL-3',
    'summary': 'Workshop Work Order',
    'author': "Jakc Labs",
    'website': 'http://www.jakc-labs.com/',
    'depends': [
        'sale','mrp','jakc_workshop'
    ],
    'data': [
        'views/jakc_sale_view.xml',
        'views/templates.xml',
        'views/res_company_view.xml',
        'wizard/add_operator_view.xml',
        'security/ir.model.access.csv',
        'report/sale_order_workshop_report.xml',
        'report/sale_order_workshop_report_templates.xml',
    ],
    'installable': True,
    'application': True,
}
