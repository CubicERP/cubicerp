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
    'name': 'Accounting Reports',
    'version': '1.0',
    'category': 'Accounting',
    'sequence': 35,
    'author': 'Cubic ERP',
    'license': 'AGPL-3',
    'summary': 'Financial and Analytic Reports',
    'description': """
Accounting Reports
==================
It transform the accounting PDF reports to useful dynamical reports. 
""",
    'website': 'https://www.cubicerp.com',
    'depends': ['account'],
    'data': [
        "views/account_report_ledger.xml",
        "views/account_report_view.xml",
        "views/account_report_template.xml",
        "wizard/account_report_ledger_view.xml",
    ],
    'qweb': [
        'static/src/xml/account_report_ledger_backend.xml',
    ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
