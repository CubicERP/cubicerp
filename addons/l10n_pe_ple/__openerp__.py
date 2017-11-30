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
    "name": "Peruvian Accounting Localization - PLE",
    "version": "1.0",
    "description": """
Programa de Libros Electrónicos

Base objects and configuration
    """,
    "author": "Cubic ERP",
    "website": "http://cubicERP.com",
    "category": "Localisation/Profile",
    "depends": [
         "account",
         "account_asset",
         "analytic",
         "base_vat",
         "stock",
         "l10n_un_unspsc",
         "l10n_pe",
         "l10n_pe_base",
         "l10n_pe_vat",
	     "base_translate_tools",
	     "base_table",
         "base_person",
         "report_excel",
         "customize",
	],
    "data":[
          "security/security.xml",
          "security/ir.model.access.csv",
          "sunat_view.xml",
          "table_view.xml",
          "data/base.table.csv",
          "data/base.element.csv",
	],
    "demo_xml": [
	],
    "update_xml": [
	],
    "active": False,
    "installable": True,
    'price': 600,
    "currency" : "USD",
    'images': [],
}
