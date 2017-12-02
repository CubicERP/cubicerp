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
    "name": "Initial Account Load",
    "version": "1.0",
    "description": """
Manage the Initital Account Load
================================

Used to manage the initial account load in easy and quickly way.

Key Features
------------
* Create new views to initial account load
* Integrated with the accounting
    """,
    "author": "Cubic ERP",
    "website": "http://cubicERP.com",
    "category": "Financial",
    "depends": [
        "account",
        "analytic",
        "account_asset",
        "product",
        ],
    "data":[
#        "account_view.xml",
        "account_load_view.xml",
        "security/account_load_security.xml",
        "security/ir.model.access.csv",
	    ],
    "demo_xml": [],
    "active": False,
    "installable": True,
    'price': 200,
    'currency': 'USD',
}
