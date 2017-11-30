# -*- encoding: utf-8 -*-
##############################################################################
#
#    Branch Cubic ERP, Enterprise Management Software
#    Copyright (C) 2016 Cubic ERP - Teradata SAC (<http://cubicerp.com>).
#
#    This program can only be used with a valid Branch Cubic ERP agreement,
#    it is forbidden to publish, distribute, modify, sublicense or sell
#    copies of the program.
#
#    The above copyright notice must be included in all copies or
#    substantial portions of the program.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT WARRANTY OF ANY KIND; without even the implied warranty
#    of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
##############################################################################

{
    "name": "Electronic Invoice",
    "version": "0.1",
    "description": """
Manage the electronic invoice
=============================

The management of electronic invoice integrate the invoices with digital signatures and certificates usually in a PKI infastructure with xml messages to a webservices to generate and validate the electronic invoices.

Key Features
------------
* Add support to manage the webservices communication to generate and validate a electronic invoice
* Generate a abstract model to manage electronic invoices from several countries

    """,
    "author": "Cubic ERP",
    "website": "http://cubicERP.com",
    "category": "Financial",
    "depends": [
        "account",
        "base_table",
        ],
    "data":[
        "security/security.xml",
        "security/ir.model.access.csv",
        "einvoice_view.xml",
	    ],
    "demo_xml": [],
    "active": False,
    "installable": True,
    "certificate" : "",
}