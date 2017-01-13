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


class AccountAccount(models.Model):
    _inherit = "account.account"

    budget_post_ids = fields.Many2many('account.budget.post', 'account_budget_rel', 'account_id', 'budget_id',
                                       string='Budget Positions')


class AccountAnalyticAaccount(models.Model):
    _inherit = "account.analytic.account"

    crossovered_budget_line = fields.One2many('crossovered.budget.lines', 'analytic_account_id', string='Budget Lines')


class account_move_line(models.Model):
    _inherit = "account.move.line"

    budget_struct_id = fields.Many2one('account.budget.struct', 'Budget Struct', domain=[('type', '=', 'normal')])

class AccountMove(models.Model):
    _inherit = 'account.move'

    budget_period_id = fields.Many2one('budget.period', string='Budget Period')
