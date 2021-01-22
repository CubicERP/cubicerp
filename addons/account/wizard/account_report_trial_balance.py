# -*- coding: utf-8 -*-

from odoo import fields, models, api


class AccountBalanceReport(models.TransientModel):
    _inherit = "account.common.account.report"
    _name = 'account.balance.report'
    _description = 'Trial Balance Report'

    journal_ids = fields.Many2many('account.journal', 'account_balance_report_journal_rel', 'account_id', 'journal_id', string='Journals', required=True, default=[])

    @api.model
    def default_get(self, fields):
        res = super(AccountBalanceReport, self).default_get(fields)
        res['report_type'] = self.env.ref('account.action_report_trial_balance').report_type
        return res

    def _print_report(self, data):
        data = self.pre_print_report(data)
        records = self.env[data['model']].browse(data.get('ids', []))
        return self.env.ref('account.action_report_trial_balance').report_action(records, data=data)
