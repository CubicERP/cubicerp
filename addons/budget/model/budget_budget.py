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

from datetime import date, datetime, timedelta

from openerp.exceptions import ValidationError

from openerp.osv import expression, osv
from openerp import models, fields, api, _
from openerp.osv.fields import selection
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

    code = fields.Char(string='Code', size=64)
    name = fields.Char(string='Name', required=True)
    complete_name = fields.Char("Full Name", compute=_get_full_name)
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
    company_id = fields.Many2one('res.company', 'Company', required=True, default=lambda self: self._default_company_id)

    def _default_company_id(self):
        return lambda self: self.pool.get('res.company')._company_default_get('budget.position')

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


class BudgetMain(models.Model):
    _name = "budget.main"
    _decription = "Main Budget"
    _inherit = ['mail.thread']

    code = fields.Char(string='Code', size=16)
    name = fields.Char(string='Name', required=True)
    type = fields.Selection([('control', 'Control'),
                             ('view', 'View')],
                            'Type', required=True, default='control')
    budget_ids = fields.One2many('budget.budget', 'budget_id', string="Budgets")

    _order = "code,name"


class BudgetBudget(models.Model):
    _name = "budget.budget"
    _description = "Budget"

    name = fields.Char(string='Name', required=True, states={'draft': [('readonly', False)]}, readonly=True)
    code = fields.Char(string='Code', size=16, states={'draft': [('readonly', False)]}, readonly=True)
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
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 states={'draft': [('readonly', False)]},
                                 readonly=True, default=lambda self: self._default_company_id)
    budget_id = fields.Many2one('budget.main', string='Main Budget', required=True, ondelete='restrict',
                                states={'draft': [('readonly', False)]}, readonly=True)
    budget_period_id = fields.Many2one('budget.period', string='Budget Period')

    def _default_company_id(self):
        return self.env['res.company']._company_default_get('budget.position')

    @api.multi
    def line_update_date(self):
        for budget in self:
            self.env['budget.budget.lines'].write([l.id for l in budget.budget_budget_line_ids],
                                                       {'date_from': budget.date_from, 'date_to': budget.date_to})
        return True

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
    @api.multi
    def _prac_amt(self):
        cr, uid, ctx, account_child = self._cr, self._uid, self._context, None
        res = {}
        result = 0.0
        if ctx is None:
            ctx = {}
        account_obj = self.env['account.account']
        analytic_obj = self.env['account.analytic.account']
        for line in self:
            # acc_ids = [x.id for x in line.general_budget_id.account_ids]
            acc_ids = line.budget_position_id.mapped('account_ids')
            if not acc_ids:
                raise osv.except_osv(_('Error!'),
                                     _("The Budget '%s' has no accounts!") % ustr(line.budget_position_id.name))
            acc_ids = acc_ids._get_children_and_consol()
            date_to = line.date_to
            date_from = line.date_from
            analytic_amount = line.value_type == 'quantity' and 'unit_amount' or 'amount'
            move_amount = line.value_type == 'quantity' and 'quantity' or 'debit-credit'
            analytic_account_ids = []
            if line.analytic_account_id:
                analytic_context = ctx.copy()
                analytic_context['analytic_child_bottom'] = True
                analytic_account_ids = analytic_obj.with_context(analytic_context).browse(
                    [line.analytic_account_id.id])._child_compute(name=['child_complete_ids'], arg=None)

                for key, value in analytic_account_ids.items():
                    account_child = list(set([key]).union(value))

                if account_child:
                    analytic_account_ids = list(set(account_child).union([line.analytic_account_id.id]))

            if line.analytic_account_id.id and line.position_restrict:
                cr.execute(
                    "SELECT SUM(" + analytic_amount + ") FROM account_analytic_line aal join account_move_line aml on (aal.move_id=aml.id) "
                                                      "WHERE aml.budget_post_id=%s AND aal.account_id in %s AND (aal.date "
                                                      "between to_date(%s,'yyyy-mm-dd') AND to_date(%s,'yyyy-mm-dd')) AND "
                                                      "aal.general_account_id=ANY(%s)",
                    (line.budget_position_id.id, analytic_account_ids, date_from, date_to, acc_ids,))
                result = cr.fetchone()[0]
            elif line.analytic_account_id.id:
                cr.execute(
                    "SELECT SUM(" + analytic_amount + ") FROM account_analytic_line WHERE account_id in %s AND (date "
                                                      "between to_date(%s,'yyyy-mm-dd') AND to_date(%s,'yyyy-mm-dd')) AND "
                                                      "general_account_id=ANY(%s)",
                    (tuple(analytic_account_ids), date_from, date_to, acc_ids,))
                result = cr.fetchone()[0]
            elif line.position_restrict:
                cr.execute(
                    "SELECT SUM(" + move_amount + ") FROM account_move_line "
                                                  "WHERE budget_post_id=%s AND (date "
                                                  "between to_date(%s,'yyyy-mm-dd') AND to_date(%s,'yyyy-mm-dd')) AND "
                                                  "account_id=ANY(%s)",
                    (line.budget_position_id.id, date_from, date_to, acc_ids,))
                result = cr.fetchone()[0]
            else:
                cr.execute(
                    "SELECT SUM(" + move_amount + ") FROM account_move_line "
                                                  "WHERE (date "
                                                  "between to_date(%s,'yyyy-mm-dd') AND to_date(%s,'yyyy-mm-dd')) AND "
                                                  "account_id=ANY(%s)",
                    (date_from, date_to, acc_ids,))
                result = cr.fetchone()[0]
            if result is None:
                result = 0.00
            res[line.id] = result * line.coefficient
        return res

    @api.multi
    def _prac(self):
        res = {}
        for line in self:
            res[line.id] = self._prac_amt()[line.id]
        return res

    @api.multi
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

            res[line.id] = theo_amt
        return res

    @api.multi
    def _theo(self):
        res = {}
        for line in self:
            res[line.id] = self._theo_amt()[line.id]
        return res

    @api.multi
    @api.depends('practical_amount', 'theoritical_amount')
    def _perc(self):
        res = {}
        for line in self:
            if line.theoritical_amount <> 0.00:
                res[line.id] = float((line.practical_amount or 0.0) / line.theoritical_amount) * 100
            else:
                res[line.id] = 0.00
        return res

    @api.multi
    def _avail(self):
        res = {}
        for line in self:
            res[line.id] = line.planned_amount - line.practical_amount
        return res

    @api.multi
    def _get_line_from_analytic(self):
        #TODO esta funcion no la llaman en ningun lugar, devuelvo los records o su lista de ids
        budget_line_ids = None
        analytic_line_obj, budget_line_obj = self.env['account.analytic.line'], self.env['budget.budget.lines']

        for analytic_line in analytic_line_obj.search([]):
            for post in analytic_line.general_account_id.budget_post_ids:
                budget_line_ids += budget_line_obj.search(
                    [
                        ('budget_position_id', '=', post.id),
                        ('analytic_account_id', '=', analytic_line.account_id.id),
                        ('state', 'in', ['draft', 'confirm', 'validate'])
                    ])
        return budget_line_ids

    @api.multi
    def _get_line_from_move(self):
        budget_line_ids = []
        for move_line in self.env['account.move.line'].browse(self.ids):
            for post in move_line.account_id.budget_post_ids:
                if move_line.analytic_account_id:
                    budget_line_ids += self.env['budget.budget.lines'].search([
                        ('budget_position_id', '=', post.id),
                        ('analytic_account_id', '=', move_line.analytic_account_id.ids),
                        ('state', 'in', ['draft', 'confirm', 'validate'])])
                else:
                    budget_line_ids += self.pool['budget.budget.lines'].search([
                        ('budget_position_id', '=', post.id),
                        ('analytic_account_id', '=', False),
                        ('state', 'in', ['draft', 'confirm', 'validate'])])
        return budget_line_ids

    @api.multi
    def _get_line_from_main_budget(self):
        budget_line_ids = None
        main_budget_obj = self.env['budget.main']
        for main_budget in main_budget_obj.search([]):
            for budget in main_budget.budget_ids:
                budget_line_ids += budget.mapped('budget_budget_line_ids')
        return budget_line_ids

    _name = "budget.budget.lines"
    _description = "Budget Line"

    sequence = fields.Integer('Sequence', default=5)
    name = fields.Char('Reference')
    budget_budget_id = fields.Many2one('budget.budget', 'Budget', ondelete='cascade', select=True,
                                            required=True)
    main_budget_id = fields.Many2one('budget.main', related='budget_budget_id.budget_id', string="Main Budget", readonly=True, store=True)

    main_budget_type = fields.Selection(related='budget_budget_id.budget_id.type', string="Main Budget Type",
                                        readonly=True, store=True)

    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    budget_position_id = fields.Many2one('budget.position', 'Budgetary Position', required=True)
    struct_budget_id = fields.Many2one('budget.struct', 'Budgetary Struct')
    value_type = fields.Selection([('amount', 'Amount'),
                                   ('quantity', 'Quantity'),
                                   ('code', 'Python Code')], string="Value Type")
    date_from = fields.Date('Start Date', required=True)
    date_to = fields.Date('End Date', required=True)
    paid_date = fields.Date('Paid Date')
    planned_amount = fields.Float('Planned Amount', required=True, digits_compute=dp.get_precision('Account'))
    practical_amount = fields.Float(compute="_prac", string='Practical Amount',
                                    digits_compute=dp.get_precision('Account'), store=True)

    theoritical_amount = fields.Float(compute="_theo", string='Theoretical Amount',
                                      digits_compute=dp.get_precision('Account'))
    available_amount = fields.Float(compute="_avail", string='Pending Amount',
                                    digits_compute=dp.get_precision('Account'))
    percentage = fields.Float(compute="_perc", string='Percentage')
    company_id = fields.Many2one(related="budget_budget_id.company_id", string='Company', store=True,
                                 readonly=True)

    position_restrict = fields.Boolean(string="Position Restricted")
    coefficient = fields.Float(string="Coefficient", required=True, digits=(16, 8), default=1.0)
    state = fields.Selection(related='budget_budget_id.state', string="State", readonly=True, store=True)

    _order = 'sequence,name'

    @api.multi
    @api.constrains('main_budget_type',
                    'analytic_account_id',
                    'budget_position_id',
                    'date_from',
                    'date_to')
    def _check_overload(self):
        for line in self:
            if line.main_budget_type == 'control':
                self._cr.execute("SELECT id FROM budget_budget_line_ids "
                                 "WHERE analytic_account_id= %s"
                                 "  AND budget_position_id= %s"
                                 "  AND main_budget_type='control' AND id <> %s"
                                 "  AND ((date_from >= %s AND date_from <= %s)"
                                 "      OR (date_to >= %s AND date_to <= %s))",
                                 (line.analytic_account_id.id,
                                  line.budget_position_id.id,
                                  line.id,
                                  line.date_from, line.date_to,
                                  line.date_from, line.date_to))
                result = self._cr.fetchone()
                if result:
                    raise ValidationError(_(
                        "Overload of control budgets in lines for budgetary position  and analytic account with same dates."))


class BudgetPeriod(models.Model):
    _name = "budget.period"

    company_id = fields.Many2one('res.company', string="Company", default=lambda s: s.env['res.users'].browse(s._uid).company_id)
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
