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

    budget_post_ids = fields.Many2many('budget.position', 'account_budget_rel', 'account_id', 'budget_id',
                                       string='Budget Positions')


class AccountAnalyticAaccount(models.Model):
    _inherit = "account.analytic.account"

    budget_budget_line_ids = fields.One2many('budget.budget.lines', 'analytic_account_id', string='Budget Lines')


class AccountPeriod(models.Model):
    _inherit = 'account.period'

    budget_period_id = fields.Many2one('budget.period', string='Budget Period')


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    budget_struct_id = fields.Many2one('budget.struct', 'Budget Struct', domain=[('type', '=', 'normal')])


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    budget_struct_id = fields.Many2one('budget.struct', 'Budget Struct', domain=[('type', '=', 'normal')])
    budget_analytic_id = fields.Many2one('account.analytic.account', 'Budget Analytic', domain=[('type', '<>', 'view')])

    def line_get_convert(self, cr, uid, x, part, date, context=None):
        res = super(AccountInvoice, self).line_get_convert(cr, uid, x, part, date, context=context)
        res['budget_struct_id'] = x.get('budget_struct_id', False)
        res['analytic_account_id'] = x.get('budget_analytic_id', False)
        return res

    def _get_first_line_values(self, inv, name, total, date_maturity, diff_currency, total_currency, ref):
        res = super(AccountInvoice, self)._get_first_line_values(inv, name, total, date_maturity, diff_currency, total_currency, ref)
        if inv.budget_struct_id:
            res['budget_struct_id'] = inv.budget_struct_id.id
        if inv.analytic_account_id:
            res['analytic_account_id'] = inv.analytic_account_id.id
        return res


class AccountVoucher(models.Model):
    _inherit = "account.voucher"

    budget_struct_id = fields.Many2one('budget.struct', 'Budget Struct', domain=[('type', '=', 'normal')])
    budget_analytic_id = fields.Many2one('account.analytic.account', 'Budget Analytic', domain=[('type', '<>', 'view')])

    @api.model
    def first_move_line_get(self, voucher_id, move_id, company_currency, current_currency):
        res = super(AccountVoucher, self).first_move_line_get(voucher_id, move_id, company_currency, current_currency)
        voucher = self.browse(voucher_id)
        if voucher.budget_struct_id:
            res['budget_struct_id'] = voucher.budget_struct_id.id
        if voucher.budget_analytic_id:
            res['analytic_account_id'] = voucher.budget_analytic_id.id
        return res
