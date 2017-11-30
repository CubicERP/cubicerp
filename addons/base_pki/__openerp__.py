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
    "name": "PKI Support",
    "version": "0.1",
    "description": """
Manage the PKI Support
======================

The management of digital certificates used by PKI infastructure.

Key Features
------------
* Add support to PKI infraestructure

    """,
    "author": "Cubic ERP",
    "website": "http://cubicERP.com",
    "category": "Encription",
    "depends": [
        "base",
        ],
    "data":[
        "security/security.xml",
        "security/ir.model.access.csv",
        "pki_view.xml",
	    ],
    "demo_xml": [],
    "active": False,
    "installable": True,
}