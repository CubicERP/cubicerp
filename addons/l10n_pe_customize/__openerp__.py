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
    'name': "l10n_pe_customize",

    'summary': """
        Adds peruvian customize""",

    'description': """
        Adds peruvian customize
    """,

    'author': "CubicERP",
    'website': "http://www.cubicerp.com",
    'category': 'customize',
    'version': '0.1',

    'depends': ['account', 'customize', 'stock', 'l10n_pe_base'],

    # always loaded
    'data': [
        "data/base.table.csv",
        "data/base.element.csv",
        'views/account_invoice.xml',
        'views/stock_picking.xml',
        'views/partner_view.xml',
    ],
}
