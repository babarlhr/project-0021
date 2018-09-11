# -*- coding: utf-8 -*-

{
    'name': 'Jakc Labs - Account Invoice Enhancement',
    'version': '9.0.0.1.0',
    'category': 'Accounting',
    'license': 'AGPL-3',
    'summary': 'Account Invoice Enchancement',
    'author': "Jakc Labs",
    'website': 'http://www.jakc-labs.com/',
    'depends': [
        'account'
    ],
    'data': [
        'views/jakc_account_invoice_view.xml',
        'report/report_account_invoice_templates.xml',
        'report/report_account_invoice_delivery.xml',
        'report/report_account_invoice_delivery_templates.xml',
    ],
    'installable': True,
    'application': True,
}
