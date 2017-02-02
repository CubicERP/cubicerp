# -*- coding: utf-8 -*-
##############################################################################
#
#    Cubic ERP, Enterprise Management Software
#    Copyright (C) 2017 Cubic ERP - Teradata SAC (<http://cubicerp.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    "name": "Budget Control",
    "version": "1.0",
    "description": """
Control all budgets of an organization
======================================

The control of budgets, enables you to track your all budgets, allowing the approve of documents based on budget availability.

Key Features
------------
* Add Budget control on Requisitions
* Add Budget control on Purchase Orders
* Add Budget control on Invoices
* Add Budget control on Vouchers
* Add Budget control on Entries Journals

Dashboard / Reports for archives will include:
----------------------------------------------
* Available Budget Report
    """,
    "author": "Cubic ERP",
    "website": "http://cubicERP.com",
    "category": "Account",
    "depends": [
        "account",
        "budget",
        "purchase",
        "purchase_requisition",
        ],
    "data":[
        "view/budget_control_view.xml",
        "view/budget_budget_view.xml",
        "view/account_view.xml",
        "data/budget_data.xml",
	    ],
    "demo_xml": [],
    "active": False,
    "installable": True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
