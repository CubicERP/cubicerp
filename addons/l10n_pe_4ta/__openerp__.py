# -*- encoding: utf-8 -*-
##############################################################################
#
#    Branch Cubic ERP, Enterprise Management Software
#    Copyright (C) 2013 Cubic ERP - Teradata SAC (<http://cubicerp.com>).
#
#    This program can only be used with a valid Branch Cubic ERP agreement,
#    it is forbidden to publish, distribute, modify, sublicense or sell 
#    copies of the program.
#
#    The adove copyright notice must be included in all copies or 
#    substancial portions of the program.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT WARRANTY OF ANY KIND; without even the implied warranty
#    of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
##############################################################################
{
    'name': 'Peru Localization Rent 4th Category',
    'category': 'Localization',
    'author': 'Cubic ERP',
    'depends': ['account',
                'l10n_pe_base'],
    'version': '1.0',
    'description': """
Manage Peruvian Rents 4th Category
==================================

    * Manage suspension certificate to rents 4th category
    * Link the suspencion with the partner
    """,
    'demo': [],
    'data':[
        'l10n_pe_4ta_view.xml',
        'partner_view.xml',
        'data/base.table.csv',
        'data/base.element.csv',
        'security/ir.model.access.csv',
    ],
    'auto_install': False,
    'installable': True,
    'price': 400,
    "currency" : "USD",
}
