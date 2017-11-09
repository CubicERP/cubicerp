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
    "name": "Peruvian Localization Basics",
    "version": "1.0",
    "description": """
Profile and basics to peruvian general localization
    """,
    "author": "Cubic ERP",
    "website": "http://cubicERP.com",
    "category": "Localisation/Profile",
    "depends": [
	    "l10n_pe",
	    "base_translate_tools",
	    "base_table",
        "product",
        "account",
	],
    "data":[
	    "data/base.table.csv",
        "data/base.element.csv",
        "product_view.xml",
        "account_view.xml",
        "company_view.xml",
        "partner_view.xml",
        "stock_view.xml",
	],
    "demo_xml": [
	],
    "active": False,
    "installable": True,
    "certificate" : "",
    'images': [],
    'price': 1400,
    'currency': 'USD',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
