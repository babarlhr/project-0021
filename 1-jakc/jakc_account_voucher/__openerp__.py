# -*- coding: utf-8 -*-

{
    'name': 'Jakc Labs - Account Voucher Enhancement',
    'version': '9.0.0.1.0',
    'category': 'General',
    'license': 'AGPL-3',
    'summary': 'Account Voucher Enchancement',
    'author': "Jakc Labs",
    'website': 'http://www.jakc-labs.com/',
    'depends': [
        'account_voucher'
    ],
    'data': [
        'views/jakc_account_voucher_view.xml',
        'views/jakc_res_users_view.xml',
        'report/account_voucher_report.xml',
        'report/account_voucher_templates.xml',
    ],
    'installable': True,
    'application': True,
}
