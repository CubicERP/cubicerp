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

from openerp import models, fields, api, _


class AccountJournal(models.Model):
    _inherit = "account.journal"

    budget_move_posted = fields.Boolean('Automatic Budget Transactions Posted', help="Mark this option to posted automatically the budget transactions")


class AccountMove(models.Model):
    _inherit = "account.move"

    budget_move_ids = fields.One2many('budget.move', 'account_move_id', string='Budget Transactions', readonly=True)

    @api.multi
    def post(self):
        for move in self:
            for line in move.line_id:
                if line.budget_struct_id:
                    tran = self.env['budget.move'].create_from_account(line)
                    if line.journal_id.budget_move_posted:
                        tran.action_done()
        return super(AccountMove, self).post()

    @api.multi
    def button_cancel(self):
        for move in self:
            for line in move.line_id:
                if line.budget_move_ids:
                    line.budget_move_ids.unlink()
        return super(AccountMove, self).button_cancel()


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    budget_move_ids = fields.One2many('budget.move', 'move_line_id', string='Budget Transactions', readonly=True)

    @api.multi
    def reconcile_partial(self, type='auto', writeoff_acc_id=False, writeoff_period_id=False, writeoff_journal_id=False):
        reconcile_id = super(AccountMoveLine, self).reconcile_partial(type=type, writeoff_acc_id=writeoff_acc_id,
                                                                writeoff_period_id=writeoff_period_id,
                                                                writeoff_journal_id=writeoff_journal_id)
        self.env['budget.move'].create_from_reconcile(reconcile_id)
        return reconcile_id

    @api.multi
    def reconcile(self, type='auto', writeoff_acc_id=False, writeoff_period_id=False, writeoff_journal_id=False):
        reconcile_id = super(AccountMoveLine, self).reconcile(type=type, writeoff_acc_id=writeoff_acc_id,
                                                              writeoff_period_id=writeoff_period_id,
                                                              writeoff_journal_id=writeoff_journal_id)
        self.env['budget.move'].create_from_reconcile(reconcile_id)
        return reconcile_id
