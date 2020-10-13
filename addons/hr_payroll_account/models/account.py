#-*- coding:utf-8 -*-
# Part of Odoo. See LICENSE_LGPL file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def reconcile(self, writeoff_acc_id=False, writeoff_journal_id=False):
        res = super(AccountMoveLine, self).reconcile(writeoff_acc_id=writeoff_acc_id, writeoff_journal_id=writeoff_journal_id)
        if self.mapped('full_reconcile_id'):
            slips = self.env['hr.payslip'].search([('move_id','in',self.mapped('move_id').ids)])
            slips.write({'state': 'paid'})
        return res

    def remove_move_reconcile(self):
        move_ids = self.full_reconcile_id.reconciled_line_ids.mapped('move_id')
        res = super(AccountMoveLine, self).remove_move_reconcile()
        slips = self.env['hr.payslip'].search([('move_id', 'in', move_ids.ids)])
        slips.write({'state': 'done'})
        return res