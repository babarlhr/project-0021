# -*- coding: utf-8 -*-
{
    'name': "Workshop Management",

    'summary': """Workshop Management System""",

    'description': """
    """,

    'author': "Jakc Labs",
    'website': "http://www.jakc-labs.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Workshop',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base',
                'hr',
                'procurement',
                'mrp',
                'website',
                'mrp_hook',
                'mrp_operations_extension'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/jakc_workshop_view.xml',
        'views/jakc_workshop_sequence.xml',
        'views/jakc_product_view.xml',
        'views/homepage_template.xml',
        'views/templates.xml',
        'security/ir.model.access.csv',
        'menu/jakc_workshop_menu.xml',
        'report/workorder_report.xml',
        'report/workorder_report_templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [

    ],
    'installable': True,
    'application': True,
}