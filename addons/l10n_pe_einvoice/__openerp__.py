# -*- coding: utf-8 -*-
##############################################################################
#
#    Cubic ERP, Enterprise and Government Management Software
#    Copyright (C) 2017 Cubic ERP S.A.C. (<http://cubicerp.com>).
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
    "name": "Electronic Invoice Peru",
    "version": "0.1",
    "description": """
Peruvian Localization - Electronic Invoice
==========================================

SUNAT SEE - Sistema de Emisión electrónica desde los sistemas del contribuyente

Key Features
------------
* Add support to peruvian electronic invoice

    """,
    "author": "Cubic ERP",
    "website": "http://cubicERP.com",
    "category": "accounting",
    "depends": [
        "base_pki",
        "base_table",
        "account",
        "account_annul",
        "account_cancel",
        "account_einvoice",
        "l10n_pe_base",
        "l10n_pe_ple",
        "l10n_pe_toponyms",
        "website",
        ],
    "data":[
        "data/base.table.csv",
        "data/base.element.csv",
        "views/company_view.xml",
        "reports/report_invoice.xml",
        "views/account_view.xml",
        "views/einvoice_view.xml",
        "views/einvoice_sequence.xml",
        "wizard/send_einvoice_wizard_view.xml",
        "wizard/refresh_wizard_view.xml",
        "wizard/request_wizard_view.xml",
        "data/server.xml",
        "security/ir.model.access.csv",
        "views/partner_view.xml",
        "views/base_view.xml",
        "views/einvoice_template.xml"
	    ],
    "demo_xml": [],
    'external_dependencies' : {
            'python' : ['pysimplesoap', 'xmlsec'],
        },
    "active": False,
    "installable": True,
}