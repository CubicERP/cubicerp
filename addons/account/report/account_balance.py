# -*- coding: utf-8 -*-

import time
from odoo import api, models, _
from odoo.exceptions import UserError


class ReportTrialBalance(models.AbstractModel):
    _name = 'report.account.report_trialbalance'

    def _get_accounts(self, accounts, display_account):
        """ compute the balance, debit and credit for the provided accounts
            :Arguments:
                `accounts`: list of accounts record,
                `display_account`: it's used to display either all accounts or those accounts which balance is > 0
            :Returns a list of dictionary of Accounts with following key and value
                `name`: Account name,
                `code`: Account code,
                `credit`: total amount of credit,
                `debit`: total amount of debit,
                `balance`: total amount of balance,
        """

        account_result = {}
        # Prepare sql query base on selected parameters from wizard
        tables, where_clause, where_params = self.env['account.move.line']._query_get()
        tables = tables.replace('"','')
        if not tables:
            tables = 'account_move_line'
        wheres = [""]
        if where_clause.strip():
            wheres.append(where_clause.strip())
        filters = " AND ".join(wheres)
        # compute the balance, debit and credit for the provided accounts
        request = ("SELECT account_move_line.account_id AS id, SUM(account_move_line.debit - account_move_line.credit) as balance" + self._select_sum_fields() +\
                   " FROM " + self._from_sum_fields(tables) + " WHERE account_id IN %s " + filters + " GROUP BY account_id" + self._group_sum_fields())
        params = (tuple(accounts.ids),) + tuple(where_params)
        self.env.cr.execute(request, params)
        for row in self.env.cr.dictfetchall():
            account_result[row.pop('id')] = row

        account_res = []
        sum_fields = self._get_sum_fields()
        total = dict((fn, 0.0) for fn in sum_fields)
        total.update({'code': '', 'name': ''})
        for account in accounts:
            res = dict((fn, 0.0) for fn in sum_fields)
            currency = account.currency_id and account.currency_id or account.company_id.currency_id
            res['code'] = account.code
            res['name'] = account.name
            balance = 0.0
            if account.id in account_result:
                balance = account_result[account.id]['balance']
                for k in sum_fields:
                    res[k] = account_result[account.id][k]
                    if display_account == 'not_zero' and not currency.is_zero(balance):
                        total[k] += res[k]
                    elif display_account == 'all' or display_account == 'movement':
                        total[k] += res[k]
            if display_account == 'all':
                account_res.append(res)
            if display_account == 'not_zero' and not currency.is_zero(balance):
                account_res.append(res)
            if display_account == 'movement' and (account.id in account_result):
                account_res.append(res)
        account_res.append(total)
        return account_res

    @api.model
    def _get_sum_fields(self):
        return ['open_debit', 'open_credit', 'debit', 'credit', 'balance_debit', 'balance_credit']

    @api.model
    def _get_sum_header(self):
        return ['Debit', 'Credit', 'Debit', 'Credit', 'Debit', 'Credit',]

    @api.model
    def _get_top_header(self):
        return [
            {'span':'2','name':_('Opening')},
            {'span':'2','name':_('Moves')},
            {'span':'2','name':_('Balance')},
        ]

    @api.model
    def _select_sum_fields(self):
        return ", SUM(CASE account_journal.type WHEN 'opening' THEN account_move_line.debit ELSE 0 END) AS open_debit, " \
               "SUM(CASE account_journal.type WHEN 'opening' THEN account_move_line.credit ELSE 0 END) AS open_credit, " \
               "SUM(CASE account_journal.type WHEN 'opening' THEN 0 WHEN 'closing' THEN 0 ELSE account_move_line.debit END) AS debit, " \
               "SUM(CASE account_journal.type WHEN 'opening' THEN 0 WHEN 'closing' THEN 0 ELSE account_move_line.credit END) AS credit, " \
               "CASE WHEN SUM(account_move_line.debit - account_move_line.credit) > 0 THEN SUM(account_move_line.debit - account_move_line.credit) ELSE 0 END AS balance_debit, " \
               "CASE WHEN SUM(account_move_line.credit - account_move_line.debit) > 0 THEN SUM(account_move_line.credit - account_move_line.debit) ELSE 0 END AS balance_credit"

    @api.model
    def _from_sum_fields(self, tables):
        tables = "%s INNER JOIN account_journal on (account_move_line.journal_id = account_journal.id) "%tables
        return tables

    @api.model
    def _group_sum_fields(self):
        return ""

    @api.model
    def get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_ids', []))
        display_account = data['form'].get('display_account')
        accounts = docs if self.model == 'account.account' else self.env['account.account'].search([])
        account_res = self.with_context(data['form'].get('used_context'))._get_accounts(accounts, display_account)

        return {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'Accounts': account_res,
            'sum_fields': self._get_sum_fields(),
            'sum_header': self._get_sum_header(),
            'top_header': self._get_top_header(),
        }
