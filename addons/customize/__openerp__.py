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
    "name": "Base Customize",
    "version": "1.0",
    "description": """
Add some general customizations to OpenERP

    """,
    "author": "Cubic ERP",
    "website": "http://cubicERP.com",
    "category": "customization",
    "depends": [
		"account_voucher",
        "account_load",
        "purchase",
        "hr_payroll",
        "stock",
        "base_translate_tools",
	    ],
	"data":[
        "hr_menu.xml",
		"account_view.xml",
        "account_menu.xml",
        "res_currency_view.xml",
        "res_company_view.xml",
        "account_sequence.xml",
        "stock_view.xml",
        "wizard/workflow_reset_view.xml",
        "data/calendar.xml",
        "data/holidays.xml",
	    ],
    "active": False,
    "installable": True,
}
