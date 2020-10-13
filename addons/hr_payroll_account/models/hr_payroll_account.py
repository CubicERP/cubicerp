#-*- coding:utf-8 -*-
# Part of Odoo. See LICENSE_LGPL file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero


class HrPayslipLine(models.Model):
    _inherit = 'hr.payslip.line'

    def _get_partner_id(self, credit_account):
        """
        Get partner_id of slip line to use in account_move_line
        """
        # use partner of salary rule or fallback on employee's address
        partner_id = False
        if credit_account:
            if self.salary_rule_id.partner_credit == 'employee':
                partner_id = self.slip_id.employee_id.address_home_id.id
            elif self.salary_rule_id.partner_credit == 'contribution':
                partner_id = self.get_register().partner_id.id
        else:
            if self.salary_rule_id.partner_debit == 'employee':
                partner_id = self.slip_id.employee_id.address_home_id.id
            elif self.salary_rule_id.partner_debit == 'contribution':
                partner_id = self.get_register().partner_id.id
        return partner_id

    def _get_analytic_id(self, credit_account):
        """
        Get account_analytic_id of slip line to use in account_move_line
        """
        analytic_id = False
        if credit_account:
            if self.salary_rule_id.analytic_credit == 'contract':
                analytic_id = self.slip_id.contract_id.analytic_account_id.id
            elif self.salary_rule_id.analytic_credit == 'run':
                analytic_id = self.slip_id.payslip_run_id.analytic_account_id.id
            elif self.salary_rule_id.analytic_credit == 'rule':
                analytic_id = self.salary_rule_id.credit_analytic_id.id
        else:
            if self.salary_rule_id.analytic_debit == 'contract':
                analytic_id = self.slip_id.contract_id.analytic_account_id.id
            elif self.salary_rule_id.analytic_debit == 'run':
                analytic_id = self.slip_id.payslip_run_id.analytic_account_id.id
            elif self.salary_rule_id.analytic_debit == 'rule':
                analytic_id = self.salary_rule_id.debit_analytic_id.id
        return analytic_id

    @api.returns('hr.contribution.register')
    def get_register(self):
        self.ensure_one()
        return self.salary_rule_id.register_id

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.depends('move_id', 'state')
    def _account_move_count(self):
        for s in self:
            s.account_move_count = len(s.move_id)
            s.amount_residual = sum(s.move_id.line_ids.filtered(lambda l: l.partner_id==s.employee_id.address_home_id and l.account_id.internal_type in ('payable','receivable')).mapped('amount_residual')) * -1.0

    date = fields.Date('Date Account', states={'draft': [('readonly', False)]}, readonly=True,
        help="Keep empty to use the period of the validation(Payslip) date.")
    journal_id = fields.Many2one('account.journal', 'Salary Journal', readonly=True, required=True,
        states={'draft': [('readonly', False)]}, default=lambda self: self.env['account.journal'].search([('type', '=', 'general')], limit=1))
    move_id = fields.Many2one('account.move', 'Accounting Entry', readonly=True, copy=False)
    account_move_count = fields.Integer(compute=_account_move_count)
    amount_residual = fields.Monetary("Residual", compute=_account_move_count)

    @api.model
    def create(self, vals):
        if 'journal_id' in self.env.context:
            vals['journal_id'] = self.env.context.get('journal_id')
        if not vals.get('journal_id') and vals.get('contract_id'):
            vals['journal_id'] = self.env['hr.contract'].browse([vals['contract_id']]).journal_id.id
        return super(HrPayslip, self).create(vals)

    @api.onchange('contract_id')
    def onchange_contract(self):
        super(HrPayslip, self).onchange_contract()
        if self.payslip_run_id.journal_id:
            self.journal_id = self.payslip_run_id.journal_id.id
        else:
            self.journal_id = self.contract_id.journal_id.id or (not self.contract_id and self.default_get(['journal_id'])['journal_id'])

    @api.multi
    def action_payslip_cancel(self):
        moves = self.mapped('move_id')
        moves.filtered(lambda x: x.state == 'posted').button_cancel()
        moves.unlink()
        return super(HrPayslip, self).action_payslip_cancel()

    @api.multi
    def action_payslip_done(self):
        res = super(HrPayslip, self).action_payslip_done()
        precision = self.env['decimal.precision'].precision_get('Payroll')

        for slip in self:
            line_ids = []
            debit_sum = 0.0
            credit_sum = 0.0
            date = slip.date or slip.date_to

            name = _('Payslip of %s') % (slip.employee_id.name)
            move_dict = {
                'narration': name,
                'ref': slip.number,
                'journal_id': slip.journal_id.id,
                'date': date,
            }
            for line in slip.details_by_salary_rule_category:
                amount = slip.credit_note and -line.total or line.total
                if float_is_zero(amount, precision_digits=precision):
                    continue
                debit_account_id = line.salary_rule_id.account_debit.id
                credit_account_id = line.salary_rule_id.account_credit.id

                if debit_account_id:
                    debit_line = (0, 0, {
                        'name': line.name,
                        'partner_id': line._get_partner_id(credit_account=False),
                        'account_id': debit_account_id,
                        'journal_id': slip.journal_id.id,
                        'date': date,
                        'debit': amount > 0.0 and amount or 0.0,
                        'credit': amount < 0.0 and -amount or 0.0,
                        'analytic_account_id': line._get_analytic_id(credit_account=False),
                        'analytic_tag_ids': [(4, i, False) for i in line.salary_rule_id.debit_analytic_tag_ids.ids],
                        'tax_line_id': line.salary_rule_id.debit_tax_id.id,
                    })
                    line_ids.append(debit_line)
                    debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']

                if credit_account_id:
                    credit_line = (0, 0, {
                        'name': line.name,
                        'partner_id': line._get_partner_id(credit_account=True),
                        'account_id': credit_account_id,
                        'journal_id': slip.journal_id.id,
                        'date': date,
                        'debit': amount < 0.0 and -amount or 0.0,
                        'credit': amount > 0.0 and amount or 0.0,
                        'analytic_account_id': line._get_analytic_id(credit_account=True),
                        'analytic_tag_ids': [(4, i, False) for i in line.salary_rule_id.credit_analytic_tag_ids.ids],
                        'tax_line_id': line.salary_rule_id.credit_tax_id.id,
                    })
                    line_ids.append(credit_line)
                    credit_sum += credit_line[2]['credit'] - credit_line[2]['debit']

            if float_compare(credit_sum, debit_sum, precision_digits=precision) == -1:
                acc_id = slip.journal_id.default_credit_account_id.id
                if not acc_id:
                    raise UserError(_('The Expense Journal "%s" has not properly configured the Credit Account!') % (slip.journal_id.name))
                adjust_credit = (0, 0, {
                    'name': _('Adjustment Entry'),
                    'partner_id': False,
                    'account_id': acc_id,
                    'journal_id': slip.journal_id.id,
                    'date': date,
                    'debit': 0.0,
                    'credit': debit_sum - credit_sum,
                })
                line_ids.append(adjust_credit)

            elif float_compare(debit_sum, credit_sum, precision_digits=precision) == -1:
                acc_id = slip.journal_id.default_debit_account_id.id
                if not acc_id:
                    raise UserError(_('The Expense Journal "%s" has not properly configured the Debit Account!') % (slip.journal_id.name))
                adjust_debit = (0, 0, {
                    'name': _('Adjustment Entry'),
                    'partner_id': False,
                    'account_id': acc_id,
                    'journal_id': slip.journal_id.id,
                    'date': date,
                    'debit': credit_sum - debit_sum,
                    'credit': 0.0,
                })
                line_ids.append(adjust_debit)
            move_dict['line_ids'] = line_ids
            move = self.env['account.move'].create(move_dict)
            slip.write({'move_id': move.id, 'date': date})
            move.post()
        return res

    def action_slip_payment(self):
        self.ensure_one()
        action_ref = self.env.ref('hr_payroll_account.action_account_slip_payment')
        if not action_ref:
            return False
        action_data = action_ref.read()[0]
        action_data['context'] = {'default_pay_move_line_ids': [(4, l.id, None) for l in self.move_id.line_ids.filtered(lambda l: l.partner_id==self.employee_id.address_home_id and l.account_id.internal_type in ('payable','receivable'))]}
        return action_data

    def _get_move_lines_ids(self):
        res = []
        for slip in self:
            full_move_ids = self.move_id.line_ids.mapped('full_reconcile_id').mapped('reconciled_line_ids').mapped('move_id')
            credit_move_ids = self.move_id.line_ids.mapped('matched_debit_ids').mapped('debit_move_id').mapped('move_id')
            debit_move_ids = self.move_id.line_ids.mapped('matched_credit_ids').mapped('credit_move_id').mapped('move_id')
            res += (self.move_id | full_move_ids | credit_move_ids | debit_move_ids).mapped('line_ids').ids
        return res

    def action_get_account_moves(self):
        self.ensure_one()
        action_ref = self.env.ref('account.action_account_moves_all_a')
        if not action_ref:
            return False
        action_data = action_ref.read()[0]
        action_data['domain'] = [('id', 'in', self._get_move_lines_ids())]
        action_data['context'] = {}
        return action_data


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    partner_debit = fields.Selection([('employee','Employee'),('contribution','Contribution Partner')], string="Debit Partner")
    partner_credit = fields.Selection([('employee','Employee'),('contribution','Contribution Partner')], string="Credit Partner")
    analytic_debit = fields.Selection([('contract','Contract'),('run','Run Payslip'),('rule','Salary Rule')], string="Debit Analytic")
    analytic_credit = fields.Selection([('contract','Contract'),('run','Run Payslip'),('rule','Salary Rule')], string="Credit Analytic")
    debit_analytic_id = fields.Many2one('account.analytic.account', 'Analytic Account Debit', domain=[('type','=','normal')])
    debit_analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic tags Debit')
    credit_analytic_id = fields.Many2one('account.analytic.account', 'Analytic Account Credit', domain=[('type','=','normal')])
    credit_analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic tags Credit')
    debit_tax_id = fields.Many2one('account.tax', 'Tax Debit')
    credit_tax_id = fields.Many2one('account.tax', 'Tax Credit')
    account_debit = fields.Many2one('account.account', 'Debit Account', domain=[('deprecated', '=', False)])
    account_credit = fields.Many2one('account.account', 'Credit Account', domain=[('deprecated', '=', False)])

class HrContract(models.Model):
    _inherit = 'hr.contract'
    _description = 'Employee Contract'

    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account', domain=[('type','=','normal')])
    journal_id = fields.Many2one('account.journal', 'Salary Journal',
                                 default=lambda self: self.env['account.journal'].search([('type', '=', 'general')], limit=1))

class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    @api.depends('slip_ids.move_id', 'state')
    def _account_move_count(self):
        for s in self:
            s.account_move_count = sum(s.slip_ids.mapped('account_move_count'))
            s.amount_residual = sum(s.slip_ids.mapped('amount_residual'))

    journal_id = fields.Many2one('account.journal', 'Salary Journal', states={'draft': [('readonly', False)]}, readonly=True)
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account',
                                          domain=[('type', '=', 'normal')])
    account_move_count = fields.Integer(compute=_account_move_count)
    amount_residual = fields.Float("Residual", compute=_account_move_count)

    def action_get_account_moves(self):
        self.ensure_one()
        action_ref = self.env.ref('account.action_account_moves_all_a')
        if not action_ref:
            return False
        action_data = action_ref.read()[0]
        action_data['domain'] = [('id', 'in', self.slip_ids._get_move_lines_ids())]
        action_data['context'] = {}
        return action_data