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

import time
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta

from openerp.exceptions import ValidationError

from openerp.osv import expression, osv
from openerp import models, fields, api, _
from openerp.tools import ustr, DEFAULT_SERVER_DATE_FORMAT
from openerp.tools.translate import _
from openerp.tools.safe_eval import safe_eval as eval

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


class BudgetStruct(models.Model):
    _name = "budget.struct"
    _description = "Budgetary Struct"

    @api.multi
    @api.depends('name','parent_id')
    def _get_full_name(self, name=None, args=None):
        for elmt in self:
            elmt.complete_name = self._get_one_full_name(elmt)

    def _get_one_full_name(self, elmt, level=6):
        if level <= 0:
            return '...'
        if elmt.parent_id:
            parent_path = self._get_one_full_name(elmt.parent_id, level - 1) + " / "
        else:
            parent_path = ''
        return parent_path + elmt.name

    code = fields.Char(string='Code', size=64, required=True)
    name = fields.Char(string='Name', required=True)
    complete_name = fields.Char("Full Name", compute=_get_full_name, store=True)
    parent_id = fields.Many2one('budget.struct', string="Parent", domain=[('type', '=', 'view')])
    type = fields.Selection([('normal', 'Normal'),
                             ('view', 'View')], string="Type", required=True)
    line_ids = fields.One2many('budget.budget.lines', 'struct_budget_id', string="Budgetary Lines")

    _order = 'code,name'
    _sql_constraints = [('code_unique', 'UNIQUE(code)', 'The code must be unique!')]

    @api.multi
    def name_get(self):
        if not self:
            return []

        reads = self.read(['name', 'code'])
        res = []
        for record in reads:
            name = record['name']
            if record['code']:
                name = record['code'] + ' ' + name
            res.append((record['id'], name))
        return res

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if self._context is None:
            self._context = {}
        if not args:
            args = []
        args = args[:]

        if name:
            if operator not in expression.NEGATIVE_TERM_OPERATORS:
                plus_percent = lambda n: n + '%'
                code_op, code_conv = {
                    'ilike': ('=ilike', plus_percent),
                    'like': ('=like', plus_percent),
                }.get(operator, (operator, lambda n: n))

                budget_struct = self.search(['|', ('code', code_op, code_conv(name)),
                                               ('name', operator, name)] + args, limit=limit)

                if not budget_struct and len(name.split()) >= 2:
                    # Separating code and name of account for searching
                    operand1, operand2 = name.split(' ', 1)  # name can contain spaces e.g. OpenERP S.A.
                    budget_struct = self.search([('code', operator, operand1), ('name', operator, operand2)] + args,
                                                  limit=limit)
            else:
                budget_struct = self.search(
                    ['&', '!', ('code', '=like', name + "%"), ('name', operator, name)] + args,
                    limit=limit)
                # as negation want to restric, do if already have results
                if budget_struct and len(name.split()) >= 2:
                    operand1, operand2 = name.split(' ', 1)  # name can contain spaces e.g. OpenERP S.A.
                    budget_struct = self.search([('code', operator, operand1), ('name', operator, operand2),
                                                   ('id', 'in', budget_struct)] + args, limit=limit)
        else:
            budget_struct = self.search(args, limit=limit)
        return budget_struct.name_get()


class BudgetPosition(models.Model):
    _name = "budget.position"
    _description = "Budgetary Position"

    code = fields.Char(string='Code', size=64)
    name = fields.Char(string='Name', required=True)
    account_ids = fields.Many2many('account.account', 'account_budget_rel', 'budget_id', 'account_id', 'Accounts')
    budget_budget_line_ids = fields.One2many('budget.budget.lines', 'budget_position_id', 'Budget Lines')
    company_id = fields.Many2one('res.company', 'Company', required=True, default=lambda s: s.env['res.company'].company_default_get('budget.budget'))

    _order = "code,name"

    @api.multi
    def name_get(self):
        if not self:
            return []

        reads = self.read(['name', 'code'])
        res = []
        for record in reads:
            name = record['name']
            if record['code']:
                name = record['code'] + ' ' + name
            res.append((record['id'], name))
        return res

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if self._context is None:
            self._context = {}
        if not args:
            args = []
        args = args[:]
        budget_position = []

        if name:
            if operator not in expression.NEGATIVE_TERM_OPERATORS:
                plus_percent = lambda n: n + '%'
                code_op, code_conv = {
                    'ilike': ('=ilike', plus_percent),
                    'like': ('=like', plus_percent),
                }.get(operator, (operator, lambda n: n))

                budget_position = self.search(['|', ('code', code_op, code_conv(name)),
                                               ('name', operator, name)] + args, limit=limit)

                if not budget_position and len(name.split()) >= 2:
                    # Separating code and name of account for searching
                    operand1, operand2 = name.split(' ', 1)  # name can contain spaces e.g. OpenERP S.A.
                    budget_position = self.search([('code', operator, operand1), ('name', operator, operand2)] + args,
                                                  limit=limit)
            else:
                budget_position = self.search(
                    ['&', '!', ('code', '=like', name + "%"), ('name', operator, name)] + args,
                    limit=limit)
                # as negation want to restric, do if already have results
                if budget_position and len(name.split()) >= 2:
                    operand1, operand2 = name.split(' ', 1)  # name can contain spaces e.g. OpenERP S.A.
                    budget_position = self.search([('code', operator, operand1), ('name', operator, operand2),
                                                   ('id', 'in', budget_position)] + args, limit=limit)
        else:
            budget_position = self.search(args, limit=limit)
        return budget_position.name_get()


class BudgetBudget(models.Model):
    _name = "budget.budget"
    _description = "Budget"

    @api.multi
    @api.depends('name','parent_id')
    def _get_full_name(self, name=None, args=None):
        for elmt in self:
            elmt.complete_name = self._get_one_full_name(elmt)

    def _get_one_full_name(self, elmt, level=6):
        if level <= 0:
            return '...'
        if elmt.parent_id:
            parent_path = self._get_one_full_name(elmt.parent_id, level - 1) + " / "
        else:
            parent_path = ''
        return parent_path + elmt.name

    @api.model
    def _get_period(self):
        periods = self.env['budget.period'].find()
        return periods and periods[0] or False

    name = fields.Char(string='Name', required=True, states={'draft': [('readonly', False)]}, readonly=True)
    code = fields.Char(string='Code', size=16, required=True, states={'draft': [('readonly', False)]}, readonly=True)
    budget_period_id = fields.Many2one('budget.period', required=True, string='Budget Period', default=_get_period,
                                       states={'draft': [('readonly', False)]}, readonly=True)
    creating_user_id = fields.Many2one('res.users', string='Responsible User', states={'draft': [('readonly', False)]},
                                       readonly=True, default=lambda self: self._uid)
    validating_user_id = fields.Many2one('res.users', 'Validate User', readonly=True)
    date_from = fields.Date(string='Start Date', required=True, states={'draft': [('readonly', False)]}, readonly=True)
    date_to = fields.Date(string='End Date', required=True, states={'draft': [('readonly', False)]}, readonly=True)
    state = fields.Selection(
        [('draft', 'Draft'), ('cancel', 'Cancelled'), ('confirm', 'Confirmed'), ('validate', 'Validated'),
         ('done', 'Done')], 'Status', select=True, required=True, readonly=True, copy=False, default='draft')
    budget_budget_line_ids = fields.One2many('budget.budget.lines', 'budget_budget_id',
                                              string='Budget Lines',
                                              states={'draft': [('readonly', False)]}, readonly=True, copy=True)
    company_id = fields.Many2one('res.company', 'Company', required=True, readonly=True,
                                 states={'draft': [('readonly', False)]},
                                 default=lambda s: s.env['res.company'].company_default_get('budget.budget'))
    parent_id = fields.Many2one('budget.budget', string='Parent Budget', domain=[('type','=','view')],
                                states={'draft': [('readonly', False)]}, readonly=True)
    type = fields.Selection([('control', 'Control'),
                             ('view', 'View')],
                            'Type', required=True, default='control')
    complete_name = fields.Char("Full Name", compute=_get_full_name, store=True)

    _order = 'code,name'

    @api.multi
    def name_get(self):
        if not self:
            return []

        reads = self.read(['name', 'code'])
        res = []
        for record in reads:
            name = record['name']
            if record['code']:
                name = record['code'] + ' ' + name
            res.append((record['id'], name))
        return res

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if not args:
            args = []
        args = args[:]

        if name:
            if operator not in expression.NEGATIVE_TERM_OPERATORS:
                plus_percent = lambda n: n + '%'
                code_op, code_conv = {
                    'ilike': ('=ilike', plus_percent),
                    'like': ('=like', plus_percent),
                }.get(operator, (operator, lambda n: n))

                element = self.search(['|', ('code', code_op, code_conv(name)),
                                               ('name', operator, name)] + args, limit=limit)

                if not element and len(name.split()) >= 2:
                    # Separating code and name of account for searching
                    operand1, operand2 = name.split(' ', 1)  # name can contain spaces e.g. OpenERP S.A.
                    element = self.search([('code', operator, operand1), ('name', operator, operand2)] + args,
                                                  limit=limit)
            else:
                element = self.search(
                    ['&', '!', ('code', '=like', name + "%"), ('name', operator, name)] + args,
                    limit=limit)
                # as negation want to restric, do if already have results
                if element and len(name.split()) >= 2:
                    operand1, operand2 = name.split(' ', 1)  # name can contain spaces e.g. OpenERP S.A.
                    element = self.search([('code', operator, operand1), ('name', operator, operand2),
                                                   ('id', 'in', element)] + args, limit=limit)
        else:
            element = self.search(args, limit=limit)
        return element.name_get()

    @api.multi
    def line_update_date(self):
        for budget in self:
            self.env['budget.budget.lines'].write([l.id for l in budget.budget_budget_line_ids],
                                                       {'date_from': budget.date_from, 'date_to': budget.date_to})
        return True

    @api.one
    @api.onchange('budget_period_id')
    def onchange_period(self):
        self.date_from = self.budget_period_id.start_date
        self.date_to = self.budget_period_id.end_date

    @api.multi
    def budget_confirm(self):
        self.write({'state': 'confirm'})
        return True

    @api.multi
    def budget_draft(self):
        self.write({'state': 'draft'})
        return True

    @api.multi
    def budget_validate(self):
        self.write({'state': 'validate', 'validating_user_id': self._uid})
        return True

    @api.multi
    def budget_cancel(self):
        self.write({'state': 'cancel'})
        return True

    @api.multi
    def budget_done(self):
        self.write({'state': 'done'})
        return True


class BudgetBudgetLines(models.Model):

    _name = "budget.budget.lines"
    _description = "Budget Line"

    @api.multi
    @api.depends('struct_budget_id','budget_position_id','analytic_account_id','python_code','value_type') # Falta apuntar a los campos del account.move.line y account.analytic.line
    def _practical_amount(self):
        cr, uid, ctx, account_child = self._cr, self._uid, self._context, None
        res = {}
        analytic_obj = self.env['account.analytic.account']

        class BrowsableObject(object):
            def __init__(self, env, dict):
                self.env = env
                self.dict = dict

            def __getattr__(self, attr):
                return attr in self.dict and self.dict.__getitem__(attr) or 0.0

        class BudgetLine(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""
            def get(self, line_name, position_code=None, date_from=None, date_to=None):

                domain = [('name', '=', line_name)]

                if position_code:
                    domain +=[('budget_position_id.code', '=', position_code)]
                if date_from:
                    domain +=[('date_to', '>=', datetime.strptime(date_from, '%Y-%m-%d'))]
                if date_to:
                    domain += [('date_from', '<=', datetime.strptime(date_to, '%Y-%m-%d'))]
                res = self.env['budget.budget.lines'].search(domain)
                return res.practical_amount if res else 0.0

        budget_line_dict = {line.name: 0.0 for line in self}
        brw_line_obj = BudgetLine(self.env, budget_line_dict)


        for line in self.sorted(key=lambda bl: bl.sequence):
            acc_ids = []

            return_value = 0.0
            if line.budget_position_id:
                acc_ids = line.budget_position_id.mapped('account_ids')
                if not acc_ids:
                    raise osv.except_osv(_('Error!'),
                                         _("The Budget Position '%s' has no accounts!") % ustr(line.budget_position_id.name))
                acc_ids = acc_ids._get_children_and_consol()
            date_to = line.date_to
            date_from = line.date_from
            analytic_account_ids = []
            if line.analytic_account_id:
                analytic_context = ctx.copy()
                analytic_context['analytic_child_bottom'] = True
                analytic_account_ids = analytic_obj.with_context(analytic_context).browse([line.analytic_account_id.id])._child_compute(name=['child_complete_ids'], arg=None)

                for key, value in analytic_account_ids.items():
                    account_child = list(set([key]).union(value))

                if account_child:
                    analytic_account_ids = list(set(account_child).union([line.analytic_account_id.id]))

            if line.analytic_account_id.id and line.budget_position_id:
                # cr.execute(
                #     "SELECT sum(unit_amount), sum(amount) FROM account_analytic_line aal join account_move_line aml on (aal.move_id=aml.id) "
                #                                       "WHERE aml.budget_struct_id=%s AND aal.account_id in %s AND (aal.date "
                #                                       "between to_date(%s,'yyyy-mm-dd') AND to_date(%s,'yyyy-mm-dd')) AND "
                #                                       "aal.general_account_id=ANY(%s)",
                #     (line.struct_budget_id.id, tuple(analytic_account_ids), date_from, date_to, acc_ids,))
                cr.execute(
                    "SELECT sum(quantity), sum(debit-credit) FROM account_move_line "
                    "WHERE budget_struct_id=%s AND analytic_account_id in %s AND (date "
                    "between to_date(%s,'yyyy-mm-dd') AND to_date(%s,'yyyy-mm-dd')) AND "
                    "account_id=ANY(%s)",
                    (line.struct_budget_id.id, tuple(analytic_account_ids), date_from, date_to, acc_ids,))
                result = cr.fetchone()
            elif line.analytic_account_id:
                # cr.execute(
                #     "SELECT sum(unit_amount), sum(amount) FROM account_analytic_line aal join account_move_line aml on (aal.move_id=aml.id) "
                #                                       "WHERE aml.budget_struct_id=%s AND aal.account_id in %s AND (aal.date "
                #                                       "between to_date(%s,'yyyy-mm-dd') AND to_date(%s,'yyyy-mm-dd'))",
                #     (line.struct_budget_id.id, tuple(analytic_account_ids), date_from, date_to,))
                cr.execute(
                    "SELECT sum(quantity), sum(debit-credit) FROM account_move_line "
                    "WHERE budget_struct_id=%s AND analytic_account_id in %s AND (date "
                    "between to_date(%s,'yyyy-mm-dd') AND to_date(%s,'yyyy-mm-dd'))",
                    (line.struct_budget_id.id, tuple(analytic_account_ids), date_from, date_to,))
                result = cr.fetchone()
            elif line.budget_position_id:
                cr.execute(
                    "SELECT sum(quantity), sum(debit-credit) FROM account_move_line "
                                                  "WHERE budget_struct_id=%s AND (date "
                                                  "between to_date(%s,'yyyy-mm-dd') AND to_date(%s,'yyyy-mm-dd')) AND "
                                                  "account_id=ANY(%s)",
                    (line.struct_budget_id.id, date_from, date_to, acc_ids,))
                result = cr.fetchone()
            else:
                cr.execute(
                    "SELECT sum(quantity), sum(debit-credit) FROM account_move_line "
                                                  "WHERE budget_struct_id=%s AND (date "
                                                  "between to_date(%s,'yyyy-mm-dd') AND to_date(%s,'yyyy-mm-dd'))",
                    (line.struct_budget_id.id,date_from, date_to,))
                result = cr.fetchone()
            quantity = 0.0 if result[0] is None else result[0]
            amount = 0.0 if result[1] is None else result[1]
            if line.value_type == 'amount':
                #line.practical_amount = amount
                return_value = amount
            elif line.value_type == 'quantity':
                #line.practical_amount = quantity
                return_value = quantity
            else: #python code
                localdict = {}
                localdict['quantity'] = quantity
                localdict['amount'] = amount
                localdict['line'] = line
                localdict['lines'] = brw_line_obj
                localdict['result'] = None
                try:
                    #return_value = eval(line.python_code, localdict, mode='exec', nocopy=True)
                    return_value = {}
                    exec line.python_code in localdict, return_value
                    return_value = 'result' in return_value and float(return_value['result']) or 0.0
                except Exception, e:
                    raise osv.except_osv(_('Error!'), _('Wrong python condition defined for budget line %s (%s).') % (
                    line.name, line.struct_budget_id.name) + "\n\n" + str(e))
            brw_line_obj.dict[line.name] += return_value
            line.practical_amount = return_value
        #return res

    @api.multi
    @api.depends('planned_amount','date_from','date_to','paid_date')
    def _theo_amt(self):
        ctx = self._context
        if ctx is None:
            ctx = {}

        res = {}
        for line in self:
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
                    theo_amt = (
                                   elapsed_timedelta.total_seconds() / line_timedelta.total_seconds()) * line.planned_amount
                else:
                    theo_amt = line.planned_amount

            line.theoritical_amount = theo_amt

    @api.multi
    @api.depends('practical_amount', 'theoritical_amount')
    def _perc(self):
        for line in self:
            if line.theoritical_amount <> 0.00:
                line.percentage = float((line.practical_amount or 0.0) / line.theoritical_amount) * 100
            else:
                line.percentage = 0.00

    @api.multi
    @api.depends('planned_amount', 'practical_amount')
    def _avail(self):
        for line in self:
            line.available_amount = line.planned_amount - line.practical_amount

    sequence = fields.Integer('Sequence', default=5)
    name = fields.Char('Code')
    budget_budget_id = fields.Many2one('budget.budget', 'Budget', ondelete='cascade', select=True,
                                            required=True, domain=[('type','<>','view')])
    parent_budget_id = fields.Many2one('budget.budget', string='Parent Budget', related="budget_budget_id.parent_id", store=True)
    struct_budget_id = fields.Many2one('budget.struct', 'Budgetary Struct', required=True, domain=[('type','<>','view')])
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    budget_position_id = fields.Many2one('budget.position', 'Budgetary Position')
    value_type = fields.Selection([('amount', 'Amount'),
                                   ('quantity', 'Quantity'),
                                   ('code', 'Python Code')], string="Value Type", default="amount", required=True)
    date_from = fields.Date('Start Date', required=True)
    date_to = fields.Date('End Date', required=True)
    paid_date = fields.Date('Paid Date')
    planned_amount = fields.Float('Planned Amount', required=True, digits_compute=dp.get_precision('Account'))
    practical_amount = fields.Float(compute="_practical_amount", string='Practical Amount',
                                    digits_compute=dp.get_precision('Account'))
    theoritical_amount = fields.Float(compute="_theo_amt", string='Theoretical Amount',
                                      digits_compute=dp.get_precision('Account'))
    available_amount = fields.Float(compute="_avail", string='Pending Amount',
                                    digits_compute=dp.get_precision('Account'))
    percentage = fields.Float(compute="_perc", string='Percentage')
    company_id = fields.Many2one("res.company", related="budget_budget_id.company_id", string='Company', store=True,
                                 readonly=True)
    python_code = fields.Text("Python Code", default='''# Available variables:
#----------------------
# amount: Debit - Credit
# quantity: Quantity
# line: budget.budget.line object (this line)
# lines: object containing the lines reference (previously computed)

# Note: returned value have to be set in the variable 'result'

result = amount''',
    )
    state = fields.Selection(related='budget_budget_id.state', string="State", readonly=True, store=True)


    _order = 'sequence,name'

    @api.multi
    @api.constrains('struct_budget_id',
                    'analytic_account_id',
                    'budget_position_id',
                    'date_from',
                    'date_to')
    def _check_overload(self):
        for line in self:
            if line.parent_budget_id.type == 'control':
                self._cr.execute("SELECT id FROM budget_budget_line_ids "
                                 "WHERE analytic_account_id= %s"
                                 "  AND budget_position_id= %s"
                                 "  AND struct_budget_id=%s AND id <> %s"
                                 "  AND ((date_from >= %s AND date_from <= %s)"
                                 "      OR (date_to >= %s AND date_to <= %s))",
                                 (line.analytic_account_id.id,
                                  line.budget_position_id.id,
                                  line.struct_budget_id.id,
                                  line.id,
                                  line.date_from, line.date_to,
                                  line.date_from, line.date_to))
                result = self._cr.fetchone()
                if result:
                    raise ValidationError(_(
                        "Overload of control budgets in lines for budgetary struct, position  and analytic account with same dates."))


class BudgetPeriod(models.Model):
    _name = "budget.period"

    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 default=lambda s: s.env['res.company'].company_default_get('budget.budget'))
    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', size=64)
    start_date = fields.Date(string='Start of period', required=True, default=fields.Date.today)
    end_date = fields.Date(string='End of period', required=True, default=fields.Date.today)
    state = fields.Selection(
        [('open', 'Open'),
         ('close', 'Close')],
        string='Status', default='open')

    @api.one
    def action_open(self):
        self.state = 'open'

    @api.one
    def action_close(self):
        self.state = 'close'

    @api.returns('self')
    @api.model
    def find(self, dt=None):
        if not dt:
            dt = fields.Date.today()
        args = [('start_date', '<=', dt), ('end_date', '>=', dt)]
        if self._context.get('company_id', False):
            args.append(('company_id', '=', self._context['company_id']))
        else:
            company_id = self.env['res.users'].browse(self._uid).company_id.id
            args.append(('company_id', '=', company_id))
        result = []
        if not result:
            result = self.search(args)
        # if not result:
        #     model, action_id = self.pool['ir.model.data'].get_object_reference(cr, uid, 'account',
        #                                                                        'action_account_period')
        #     msg = _('There is no period defined for this date: %s.\nPlease go to Configuration/Periods.') % dt
        #     raise openerp.exceptions.RedirectWarning(msg, action_id, _('Go to the configuration panel'))
        return result
