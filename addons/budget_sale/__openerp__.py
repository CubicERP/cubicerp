# -*- coding: utf-8 -*-
{
    'name': "Budgets Sale Management",

    'summary': """
        Integration module of budget accounting with the flow of sales""",

    'description': """
        Integration module of budget accounting with the flow of sales
    """,

    'author': "OpenERP SA",
    'website': "https://www.odoo.com/page/accounting",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Accounting & Finance',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['budget', 'sale'],

    # always loaded
    'data': [
        'view/sale_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}