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
    'name': "Budget Control with Sale Management",

    'summary': """
        Integration module of budget control with the flow of sales""",

    'description': """
        Integration module of budget control with the flow of sales
    """,

    'author': "Cubic ERP",
    'website': "http://www.cubicerp.com",

    'category': 'Accounting & Finance',
    'version': '1.0',

    'depends': ['budget_control',
                'budget_sale'],
    'data': [
        'view/sale_view.xml',
        'view/budget_control_view.xml',
    ],
    'demo': [
        'demo.xml',
    ],
}