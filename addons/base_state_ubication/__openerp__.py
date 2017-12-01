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
    "name": "States Inherited (Recursive Ubication)",
    "version": "1.0",
    "description": """
        Add parent state to standard state and transform the states on recursive ubication
        """,
    "author": "Cubic ERP",
    "website": "http://cubicERP.com",
    "category": "Others",
    "depends": ["base"],
    "data":["res_state_view.xml",
            "res_partner_view.xml",
            ],
    "demo_xml": [ ],
    "update_xml": [ ],
    "active": False,
    "installable": True,
    "certificate" : "",
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
