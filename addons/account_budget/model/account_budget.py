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

from openerp.osv import fields, osv, expression
from openerp.tools import ustr, DEFAULT_SERVER_DATE_FORMAT
from openerp.tools.translate import _

import openerp.addons.decimal_precision as dp


# ---------------------------------------------------------
# Utils
# ---------------------------------------------------------
def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))

def strToDatetime(strdate):
    return datetime.strptime(strdate, DEFAULT_SERVER_DATE_FORMAT)

# ---------------------------------------------------------
# Budgets
# ---------------------------------------------------------
class account_budget_struct(osv.osv):
    _name = "account.budget.struct"
    _description = "Budgetary Struct"
    _columns = {
        'code': fields.char('Code', size=64),
        'name': fields.char('Name', required=True),
        'parent_id': fields.many2one('account.budget.struct', string="Parent", domain=[('type','=','view')]),
        'type': fields.selection([('normal','Normal'),
                                  ('view','View')], string="Type", required=True),
        'line_ids': fields.one2many('crossovered.budget.lines','struct_budget_id', string="Budgetary Lines"),
    }
    _order = 'code,name'
    _sql_constraints = [('code_unique','unique(code)','The code must be unique!')]


class account_budget_post(osv.osv):
    _name = "account.budget.post"
    _description = "Budgetary Position"
    _columns = {
        'code': fields.char('Code', size=64),
        'name': fields.char('Name', required=True),
        'account_ids': fields.many2many('account.account', 'account_budget_rel', 'budget_id', 'account_id', 'Accounts'),
        'crossovered_budget_line': fields.one2many('crossovered.budget.lines', 'general_budget_id', 'Budget Lines'),
        'company_id': fields.many2one('res.company', 'Company', required=True),
    }
    _defaults = {
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company')._company_default_get(cr, uid, 'account.budget.post', context=c),

    }
    _order = "code,name"

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        if isinstance(ids, (int, long)):
            ids = [ids]
        reads = self.read(cr, uid, ids, ['name', 'code'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['code']:
                name = record['code'] + ' ' + name
            res.append((record['id'], name))
        return res

    def name_search(self, cr, user, name, args=None, operator='ilike', context=None, limit=100):
        if context is None:
            context = {}
        if not args:
            args = []
        args = args[:]
        ids = []

        if name:
            if operator not in expression.NEGATIVE_TERM_OPERATORS:
                plus_percent = lambda n: n + '%'
                code_op, code_conv = {
                    'ilike': ('=ilike', plus_percent),
                    'like': ('=like', plus_percent),
                }.get(operator, (operator, lambda n: n))

                ids = self.search(cr, user, ['|', ('code', code_op, code_conv(name)),
                                             ('name', operator, name)] + args, limit=limit, context=context)

                if not ids and len(name.split()) >= 2:
                    # Separating code and name of account for searching
                    operand1, operand2 = name.split(' ', 1)  # name can contain spaces e.g. OpenERP S.A.
                    ids = self.search(cr, user, [('code', operator, operand1), ('name', operator, operand2)] + args,
                                      limit=limit, context=context)
            else:
                ids = self.search(cr, user, ['&', '!', ('code', '=like', name + "%"), ('name', operator, name)] + args,
                                  limit=limit, context=context)
                # as negation want to restric, do if already have results
                if ids and len(name.split()) >= 2:
                    operand1, operand2 = name.split(' ', 1)  # name can contain spaces e.g. OpenERP S.A.
                    ids = self.search(cr, user, [('code', operator, operand1), ('name', operator, operand2),
                                                 ('id', 'in', ids)] + args, limit=limit, context=context)
        else:
            ids = self.search(cr, user, args, context=context, limit=limit)
        return self.name_get(cr, user, ids, context=context)


class budget_budget(osv.osv):
    _name = "budget.budget"
    _decription = "Main Budget"
    _inherit = ['mail.thread']

    _columns = {
        'code': fields.char('Code', size=16),
        'name': fields.char('Name', required=True),
        'type': fields.selection([('control', 'Control'),
                                    ('view', 'View')], 'Type', required=True),
        'budget_ids': fields.one2many('crossovered.budget', 'budget_id', string="Budgets"),
    }
    _defaults = {
        'type': 'control',
    }
    _order = "code,name"

class crossovered_budget(osv.osv):
    _name = "crossovered.budget"
    _description = "Budget"

    _columns = {
        'name': fields.char('Name', required=True, states={'draft':[('readonly',False)]}, readonly=True),
        'code': fields.char('Code', size=16, states={'draft':[('readonly',False)]}, readonly=True),
        'creating_user_id': fields.many2one('res.users', 'Responsible User', states={'draft':[('readonly',False)]}, readonly=True),
        'validating_user_id': fields.many2one('res.users', 'Validate User', readonly=True),
        'date_from': fields.date('Start Date', required=True, states={'draft':[('readonly',False)]}, readonly=True),
        'date_to': fields.date('End Date', required=True, states={'draft':[('readonly',False)]}, readonly=True),
        'state' : fields.selection([('draft','Draft'),('cancel', 'Cancelled'),('confirm','Confirmed'),('validate','Validated'),('done','Done')], 'Status', select=True, required=True, readonly=True, copy=False),
        'crossovered_budget_line': fields.one2many('crossovered.budget.lines', 'crossovered_budget_id', 'Budget Lines', states={'draft':[('readonly',False)]}, readonly=True, copy=True),
        'company_id': fields.many2one('res.company', 'Company', required=True, states={'draft':[('readonly',False)]}, readonly=True),
        'budget_id': fields.many2one('budget.budget', 'Main Budget', required=True, ondelete='restrict',
                                     states={'draft':[('readonly',False)]}, readonly=True)
    }

    _defaults = {
        'state': 'draft',
        'creating_user_id': lambda self, cr, uid, context: uid,
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company')._company_default_get(cr, uid, 'account.budget.post', context=c)
    }

    def line_update_date(self, cr, uid, ids, context=None):
        for budget in self.browse(cr, uid, ids, context=context):
            self.pool['crossovered.budget.lines'].write(cr, uid, [l.id for l in budget.crossovered_budget_line],
                                                        {'date_from': budget.date_from ,'date_to': budget.date_to},
                                                        context=context)
        return True

    def budget_confirm(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {
            'state': 'confirm'
        }, context=context)
        return True

    def budget_draft(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {
            'state': 'draft'
        }, context=context)
        return True

    def budget_validate(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {
            'state': 'validate',
            'validating_user_id': uid,
        }, context=context)
        return True

    def budget_cancel(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {
            'state': 'cancel'
        }, context=context)
        return True

    def budget_done(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {
            'state': 'done'
        }, context=context)
        return True


class crossovered_budget_lines(osv.osv):

    def _prac_amt(self, cr, uid, ids, context=None):
        res = {}
        result = 0.0
        if context is None: 
            context = {}
        account_obj = self.pool.get('account.account')
        for line in self.browse(cr, uid, ids, context=context):
            acc_ids = [x.id for x in line.general_budget_id.account_ids]
            if not acc_ids:
                raise osv.except_osv(_('Error!'),_("The Budget '%s' has no accounts!") % ustr(line.general_budget_id.name))
            acc_ids = account_obj._get_children_and_consol(cr, uid, acc_ids, context=context)
            date_to = line.date_to
            date_from = line.date_from
            analytic_amount = line.general_budget_id.value_type == 'quantity' and 'unit_amount' or 'amount'
            move_amount = line.general_budget_id.value_type == 'quantity' and 'quantity' or 'debit-credit'
            analytic_account_ids = []
            if line.analytic_account_id:
                analytic_context = context.copy()
                analytic_context['analytic_child_bottom'] = True
                analytic_account_ids = \
                self.pool.get('account.analytic.account')._child_compute(cr, uid, [line.analytic_account_id.id],
                                                                         False, [], context=analytic_context)[line.analytic_account_id.id]
                analytic_account_ids = tuple(analytic_account_ids + [line.analytic_account_id.id])

            if line.analytic_account_id.id and line.position_restrict:
                cr.execute("SELECT SUM("+analytic_amount+") FROM account_analytic_line aal join account_move_line aml on (aal.move_id=aml.id) "
                           "WHERE aml.budget_post_id=%s AND aal.account_id in %s AND (aal.date "
                           "between to_date(%s,'yyyy-mm-dd') AND to_date(%s,'yyyy-mm-dd')) AND "
                           "aal.general_account_id=ANY(%s)", (line.general_budget_id.id,analytic_account_ids, date_from, date_to, acc_ids,))
                result = cr.fetchone()[0]
            elif line.analytic_account_id.id:
                cr.execute("SELECT SUM("+analytic_amount+") FROM account_analytic_line WHERE account_id in %s AND (date "
                       "between to_date(%s,'yyyy-mm-dd') AND to_date(%s,'yyyy-mm-dd')) AND "
                       "general_account_id=ANY(%s)", (analytic_account_ids, date_from, date_to,acc_ids,))
                result = cr.fetchone()[0]
            elif line.position_restrict:
                cr.execute(
                    "SELECT SUM("+move_amount+") FROM account_move_line "
                    "WHERE budget_post_id=%s AND (date "
                    "between to_date(%s,'yyyy-mm-dd') AND to_date(%s,'yyyy-mm-dd')) AND "
                    "account_id=ANY(%s)",
                    (line.general_budget_id.id, date_from, date_to, acc_ids,))
                result = cr.fetchone()[0]
            else:
                cr.execute(
                    "SELECT SUM("+move_amount+") FROM account_move_line "
                    "WHERE (date "
                    "between to_date(%s,'yyyy-mm-dd') AND to_date(%s,'yyyy-mm-dd')) AND "
                    "account_id=ANY(%s)",
                    (date_from, date_to, acc_ids,))
                result = cr.fetchone()[0]
            if result is None:
                result = 0.00
            res[line.id] = result * line.coefficient
        return res

    def _prac(self, cr, uid, ids, name, args, context=None):
        res={}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = self._prac_amt(cr, uid, [line.id], context=context)[line.id]
        return res

    def _theo_amt(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            today = datetime.now()

            if line.paid_date:
                if strToDate(line.date_to) <= strToDate(line.paid_date):
                    theo_amt = 0.00
                else:
                    theo_amt = line.planned_amount
            else:
                line_timedelta = strToDatetime(line.date_to) - strToDatetime(line.date_from)
                elapsed_timedelta = today - (strToDatetime(line.date_from))

                if elapsed_timedelta.days < 0:
                    # If the budget line has not started yet, theoretical amount should be zero
                    theo_amt = 0.00
                elif line_timedelta.days > 0 and today < strToDatetime(line.date_to):
                    # If today is between the budget line date_from and date_to
                    theo_amt = (elapsed_timedelta.total_seconds() / line_timedelta.total_seconds()) * line.planned_amount
                else:
                    theo_amt = line.planned_amount

            res[line.id] = theo_amt
        return res

    def _theo(self, cr, uid, ids, name, args, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = self._theo_amt(cr, uid, [line.id], context=context)[line.id]
        return res

    def _perc(self, cr, uid, ids, name, args, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            if line.theoritical_amount <> 0.00:
                res[line.id] = float((line.practical_amount or 0.0) / line.theoritical_amount) * 100
            else:
                res[line.id] = 0.00
        return res

    def _avail(self, cr, uid, ids, name, args, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = line.planned_amount - line.practical_amount
        return res

    def _get_line_from_analytic(self, cr, uid, ids, context=None):
        budget_line_ids = []
        for line in self.pool['account.analytic.line'].browse(cr, uid, ids, context=context):
            for post in line.general_account_id.budget_post_ids:
                budget_line_ids += self.pool['crossovered.budget.lines'].search(cr, uid, [('general_budget_id', '=', post.id),
                                                         ('analytic_account_id', '=', line.account_id.id),
                                                         ('state', 'in', ['draft', 'confirm', 'validate'])],
                                               context=context)
        return budget_line_ids

    def _get_line_from_move(self, cr, uid, ids, context=None):
        budget_line_ids = []
        for move_line in self.pool['account.move.line'].browse(cr, uid, ids, context=context):
            for post in move_line.account_id.budget_post_ids:
                if move_line.analytic_account_id:
                    budget_line_ids += self.pool['crossovered.budget.lines'].search(cr, uid, [('general_budget_id', '=', post.id),
                                                             ('analytic_account_id', '=', move_line.analytic_account_id.ids),
                                                             ('state', 'in', ['draft', 'confirm', 'validate'])],
                                                   context=context)
                else:
                    budget_line_ids += self.pool['crossovered.budget.lines'].search(cr, uid, [('general_budget_id', '=', post.id),
                                                             ('analytic_account_id', '=', False),
                                                             ('state', 'in', ['draft', 'confirm', 'validate'])],
                                                   context=context)
        return budget_line_ids

    def _get_line_from_main_budget(self, cr, uid, ids, context=None):
        budget_line_ids = []
        for main_budget in self.pool['budget.budget'].browse(cr, uid, ids, context=context):
            for budget in main_budget.budget_ids:
                budget_line_ids += [l.id for l in budget.crossovered_budget_line]
        return budget_line_ids

    _name = "crossovered.budget.lines"
    _description = "Budget Line"
    _columns = {
        'sequence': fields.integer('Sequence'),
        'name': fields.char('Reference'),
        'crossovered_budget_id': fields.many2one('crossovered.budget', 'Budget', ondelete='cascade', select=True, required=True),
        'main_budget_id': fields.related('crossovered_budget_id','budget_id', string="Main Budget", type="many2one",
                                         relation="budget.budget", readonly=True, store={
                'crossovered.budget': (lambda s, cr, u, i, c: [e for j in
                                                               [[l.id for l in b.crossovered_budget_line] for b in
                                                                s.pool['crossovered.budget'].browse(cr, u, i)] for e in
                                                               j], ['budget_id'], 10),
                'crossovered.budget.lines': (lambda s, cr, u, i, c: i, ['crossovered_budget_id'], 10)
            }),
        'main_budget_type': fields.related('crossovered_budget_id', 'budget_id', 'type', string="Main Budget Tyupe",
                                           type="char", readonly=True, store={
                'budget.budget': (_get_line_from_main_budget, ['type'], 10),
                'crossovered.budget': (lambda  s,cr,u,i,c: [e for j in [[l.id for l in b.crossovered_budget_line] for b in s.pool['crossovered.budget'].browse(cr,u,i)] for e in j],['budget_id'],10),
                'crossovered.budget.lines': (lambda s, cr, u, i, c: i, ['crossovered_budget_id'], 10)
            }),
        'analytic_account_id': fields.many2one('account.analytic.account', 'Analytic Account'),
        'general_budget_id': fields.many2one('account.budget.post', 'Budgetary Position',required=True),
        'struct_budget_id': fields.many2one('account.budget.struct', 'Budgetary Struct'),
        'value_type': fields.selection([('amount','Amount'),
                                        ('quantity','Quantity'),
                                        ('code','Python Code')], string="Value Type"),
        'date_from': fields.date('Start Date', required=True),
        'date_to': fields.date('End Date', required=True),
        'paid_date': fields.date('Paid Date'),
        'planned_amount':fields.float('Planned Amount', required=True, digits_compute=dp.get_precision('Account')),
        'practical_amount': fields.function(_prac, string='Practical Amount', type='float',
                                            digits_compute=dp.get_precision('Account'),
                                            store={'account.analytic.line': (_get_line_from_analytic,
                                                                             ['account_id', 'date',
                                                                              'general_account_id', 'amount',
                                                                              'unit_amount'], 10),
                                                   'account.move.line': (_get_line_from_move,
                                                                         ['budget_struct_id', 'date', 'account_id',
                                                                          'debit', 'credit', 'quantity'], 10),
                                                   'crossovered.budget.lines': (lambda s,cr,u,i,c: i,['crossovered_budget_id',
                                                                                                      'analytic_account_id',
                                                                                                      'general_budget_id',
                                                                                                      'date_from','date_to',
                                                                                                      'position_restrict',
                                                                                                      'coefficient'],10)}),
        'theoritical_amount':fields.function(_theo, string='Theoretical Amount', type='float', digits_compute=dp.get_precision('Account')),
        'available_amount': fields.function(_avail, string='Pending Amount', type='float', digits_compute=dp.get_precision('Account')),
        'percentage':fields.function(_perc, string='Percentage', type='float'),
        'company_id': fields.related('crossovered_budget_id', 'company_id', type='many2one', relation='res.company', string='Company', store=True, readonly=True),
        'position_restrict': fields.boolean("Position Restricted"),
        'coefficient': fields.float("Coefficient", required=True, digits=(16,8)),
        'state': fields.related('crossovered_budget_id','state', string="State", type="char", readonly=True, store={
            'crossovered.budget': (lambda s, cr, u, i, c: [e for j in
                                                           [[l.id for l in b.crossovered_budget_line] for b in
                                                            s.pool['crossovered.budget'].browse(cr, u, i)] for e in j],
                                   ['state'], 10),
            'crossovered.budget.lines': (lambda s, cr, u, i, c: i, ['crossovered_budget_id'], 10)
        })
    }
    _defaults = {
        'sequence': 5,
        'coefficient': 1.0,
    }
    _order = 'sequence,name'

    def _check_overload(self, cr, uid, ids, context=None):
        for line in self.browse(cr, uid, ids, context=context):
            if line.main_budget_type == 'control':
                cr.execute("select id from crossovered_budget_lines "
                           "where analytic_account_id= %s"
                           "  and general_budget_id= %s"
                           "  and main_budget_type='control' and id <> %s"
                           "  and ((date_from >= %s and date_from <= %s)"
                           "      or (date_to >= %s and date_to <= %s))",
                           (line.analytic_account_id.id,
                            line.general_budget_id.id,
                            line.id,
                            line.date_from, line.date_to,
                            line.date_from, line.date_to))
                result = cr.fetchone()
                if result:
                    return False
        return True

    _constraints = [(_check_overload, "Overload of control budgets in lines for budgetary position  and analytic account with same dates.",
                     ['main_budget_type', 'analytic_account_id', 'general_budget_id', 'date_from', 'date_to'])]
