# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

from datetime import date, datetime

# from openerp.osv import fields, osv, expression
from openerp import models, fields, api, _
from openerp.tools import ustr, DEFAULT_SERVER_DATE_FORMAT
from openerp.tools.translate import _

import openerp.addons.decimal_precision as dp


class account_entries_report(models.Model):
    _name = "account.entries.report"
    _inherit = "account.entries.report"

    budget_struct_id = fields.Many2one('account.budget.struct', string='Budget Struct', readonly=True)

    def _get_select(self):
        res = super(account_entries_report, self)._get_select()
        return """%s,
         l.budget_struct_id as budget_struct_id
        """%(res)
