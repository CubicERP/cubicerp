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
    "name": "Archives",
    "version": "1.0",
    "description": """
Manage all archives of an organization
======================================

The management of archives, enables you to track your all documents in easy and secure way.

Key Features
------------
* Manage documentes related to quality systems
* Manage your documentary process
* Optimize the comunication inside the organization

Dashboard / Reports for archives will include:
----------------------------------------------
* Archives Report
    """,
    "author": "Cubic ERP",
    "website": "http://cubicERP.com",
    "category": "Tools",
    "depends": [
        "hr",
        "document",
        "mail",
        "stock",
        ],
    "data": [
        "wizard/document_delegate_view.xml",
        "wizard/attachment_wizard_view.xml",
        "wizard/transition_response_view.xml",
        "transition_response_template.xml",
        "archives_view.xml",
        'archives.xml',
        ],
    "demo_xml": [],
    "active": False,
    "installable": True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
