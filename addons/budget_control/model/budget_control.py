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

from openerp import models, fields, api, exceptions, _


class BudgetMove(models.Model):
    _name = "budget.move"
    _description = "Budget Move Transaction"

    @api.model
    def _get_period(self):
        periods = self.env['budget.period'].find()
        return periods and periods[0] or False

    @api.multi
    @api.depends('line_ids','line_ids.available','line_ids.committed','line_ids.provision','line_ids.paid')
    def _compute_amount(self):
        for move in self:
            available = committed = provision = paid = total_amount = 0.0
            for line in move.line_ids:
                available += line.available
                committed += line.committed
                provision += line.provision
                paid += line.paid
                if line.available > 0.0:
                    total_amount += line.available
                if line.committed > 0.0:
                    total_amount += line.committed
                if line.provision > 0.0:
                    total_amount += line.provision
                if line.paid > 0.0:
                    total_amount += line.paid

            move.available = available
            move.committed = committed
            move.provision = provision
            move.paid = paid
            move.total_amount = total_amount

    name = fields.Char("Name", required=True, default="/", states={'draft': [('readonly', False)]}, readonly=True)
    ref = fields.Char("Reference", states={'draft': [('readonly', False)]}, readonly=True)
    date = fields.Date("Date", required=True, default=fields.Date.today, states={'draft': [('readonly', False)]}, readonly=True)
    period_id = fields.Many2one('budget.period', string="Period", required=True, default=_get_period,
                                states={'draft': [('readonly', False)]}, readonly=True)
    line_ids = fields.One2many('budget.move.line', 'move_id', string="Lines", states={'draft': [('readonly', False)]}, readonly=True)
    move_line_id = fields.Many2one('account.move.line', string="Move Line",
                                states={'draft': [('readonly', False)]}, readonly=True)
    account_move_id = fields.Many2one('account.move', string="Account Entry", related="move_line_id.move_id",
                                      readonly=True, store=True)
    account_journal_id = fields.Many2one('account.journal', string="Account Journal", readonly=True, store=True,
                                         related="move_line_id.move_id.journal_id")
    state = fields.Selection([('draft','Draft'),
                              ('done','Done')], string="State", readonly=True, default='draft')
    company_id = fields.Many2one('res.company', 'Company', required=True, readonly=True,
                                 states={'draft': [('readonly', False)]},
                                 default=lambda s: s.env['res.company'].company_default_get('budget.budget'))
    available = fields.Float("Available", compute=_compute_amount)
    committed = fields.Float("Committed", compute=_compute_amount)
    provision = fields.Float("Provision", compute=_compute_amount)
    paid = fields.Float("Paid", compute=_compute_amount)
    total_amount = fields.Float("Total Amount", compute=_compute_amount)

    @api.one
    def unlink(self):
        if self.state == 'done':
            raise exceptions.ValidationError(_("The Budget Transaction %s must be in draft state, to be deleted!")%(self.name))
        return super(BudgetMove, self).unlink()

    @api.model
    def create(self, vals):
        if vals.get('name','/') == '/':
            vals['name'] = self.env['ir.sequence'].get('budget.control.move')
        return super(BudgetMove, self).create(vals)

    @api.one
    def action_draft(self):
        self.state = 'draft'

    @api.one
    def action_done(self):
        for line in self.line_ids:
            if line.state <> 'valid':
                raise exceptions.ValidationError(_("The lines must be in valid state. The line %s (%s) is invalid")%(line.name,line.struct_id.get_name()))
        self.state = 'done'

    def _create_move_values(self, line):
        res = {
            'ref': line.move_id.ref,
            'date': line.move_id.date,
            'move_line_id': line.id,
        }
        if line.move_id.period_id.budget_period_id:
            res['period_id'] = line.move_id.period_id.budget_period_id.id
        return res

    def _create_lines_values(self, move, line, amount=None, struct_id=None, analytic_id=None):
        if amount is None:
            amount = line.debit - line.credit
        if struct_id is None:
            struct_id = line.budget_struct_id.id
        if analytic_id is None:
            analytic_id = line.analytic_account_id.id
        l1 = {
            'move_id': move.id,
            'name': line.name,
            'struct_id': struct_id,
        }
        l2 = {
            'move_id': move.id,
            'name': line.name,
            'struct_id': struct_id,
        }
        if analytic_id:
            l1['analytic_id'] = analytic_id
            l2['analytic_id'] = analytic_id
        if line.partner_id:
            l1['partner_id'] = line.partner_id.id
            l2['partner_id'] = line.partner_id.id
        if line.move_id.journal_id.type in ('cash','bank'):
            l1['paid'] = amount * -1.0
            l2['provision'] = amount
        elif line.move_id.journal_id.type in ('sale','sale_refund','purchase','purchase_refund'):
            l1['provision'] = amount
            l2['committed'] = amount * -1.0
        else:
            raise exceptions.ValidationError(_("The journal kind %s is not supported to make automatic budget "
                                               "transactions. Make a manually budget transaction for the line %s!") %
                                             (line.move_id.journal_id.type,line.name))
        return [l1, l2]

    def create_from_account(self, line):
        move = self.create(self._create_move_values(line))
        for line_dict in self._create_lines_values(move, line):
            self.env['budget.move.line'].create(line_dict)
        return move

    def create_from_reconcile(self, reconcile_id):
        reconcile = self.env['account.move.reconcile'].browse(reconcile_id)
        cash = []
        prom = {}
        vals = []
        for line in reconcile.line_id:
            if line.journal_id.type in ('cash','bank') and not line.budget_struct_id:
                cash += [line]
            elif line.journal_id.type not in ('cash','bank') and line.budget_struct_id:
                prom[(line.budget_struct_id.id,line.analytic_account_id.id,line.partner_id.id)] = \
                    prom.get((line.budget_struct_id.id,line.analytic_account_id.id,line.partner_id.id), 0.0) + \
                    (line.debit - line.credit)
                vals.append((line.debit - line.credit))
        total_vals = sum(vals)
        if cash and total_vals:
            for c in cash:
                move = self.create(self._create_move_values(c))
                for k in prom:
                    amount = (c.debit-c.credit) * prom[k] / total_vals
                    for line_dict in self._create_lines_values(move, c, amount=amount, struct_id=k[0],analytic_id=k[1]):
                        self.env['budget.move.line'].create(line_dict)


class BudgetMoveLine(models.Model):
    _name = "budget.move.line"
    _description = "Budget Move Line"

    name = fields.Char("Name", required=True)
    move_id = fields.Many2one("budget.move", string="Move", required=True, ondelete="cascade")
    period_id = fields.Many2one('budget.period', string="Period", related="move_id.period_id", readonly=True, store=True)
    company_id = fields.Many2one("res.company", related="move_id.company_id", string='Company', store=True, readonly=True)
    struct_id = fields.Many2one('budget.struct', string="Struct", required=True,
                                domain=[('type','=','normal')])
    analytic_id = fields.Many2one('account.analytic.account', string="Analytic Account")
    partner_id = fields.Many2one('res.partner', string="Partner")
    available = fields.Float("Available")
    committed = fields.Float("Committed")
    provision = fields.Float("Provision")
    paid = fields.Float("Paid")
    state = fields.Selection([('draft','Draft'),
                              ('valid','Valid')], string="State", readonly=True, default='valid')

    @api.model
    def create(self, vals):
        if 'available' in vals or 'committed' in vals or 'provision' in vals or 'paid' in vals:
            res = vals.get('available', 0.0) + vals.get('committed', 0.0) + vals.get('provision', 0.0) + vals.get('paid', 0.0)
            valid_ids = []
            for line in self.env['budget.move'].browse(vals['move_id']).line_ids:
                res += line.available + line.committed + line.provision + line.paid
                valid_ids += line.state == 'draft' and [line] or []
            if res == 0.0:
                vals['state'] = 'valid'
                for line in valid_ids:
                    line.state = 'valid'
            else:
                vals['state'] = 'draft'
        return super(BudgetMoveLine, self).create(vals)

    @api.one
    def write(self, vals):
        if 'available' in vals or 'committed' in vals or 'provision' in vals or 'paid' in vals:
            res = vals.get('available', 0.0) + vals.get('committed', 0.0) + vals.get('provision', 0.0) + vals.get('paid', 0.0)
            move_id = vals.get('move_id', self.move_id.id)
            valid_ids = []
            for line in self.env['budget.move'].browse(move_id).line_ids:
                if line.id <> self.id:
                    res += line.available + line.committed + line.provision + line.paid
                    valid_ids += line.state=='draft' and [line] or []
            if res == 0.0:
                vals['state'] = 'valid'
                for line in valid_ids:
                    line.state = 'valid'
            else:
                vals['state'] = 'draft'
        return super(BudgetMoveLine, self).write(vals)

    @api.multi
    def unlink(self):
        for del_line in self:
            res = 0.0
            line_ids = []
            for line in del_line.move_id.line_ids:
                if line.id <> del_line.id:
                    res += line.available + line.committed + line.provision + line.paid
                    line_ids += [line]
            if line_ids:
                line_ids.write({'state': res == 0.0 and 'valid' or 'draft'})
        return super(BudgetMoveLine, self).unlink()
