##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
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

from openerp.report import report_sxw
from common_report_header import common_report_header
from openerp.tools.translate import _
from openerp.osv import osv


class report_account_common(report_sxw.rml_parse, common_report_header):

    def __init__(self, cr, uid, name, context=None):
        super(report_account_common, self).__init__(cr, uid, name, context=context)
        self.localcontext.update( {
            'get_lines': self.get_lines,
            'time': time,
            'get_fiscalyear': self._get_fiscalyear,
            'get_account': self._get_account,
            'get_start_period': self.get_start_period,
            'get_end_period': self.get_end_period,
            'get_filter': self._get_filter,
            'get_start_date':self._get_start_date,
            'get_end_date':self._get_end_date,
            'get_target_move': self._get_target_move,
            'get_analytic': self._get_analytic,
            'get_multi_names': self._get_multi_names,
        })
        self.context = context

    def set_context(self, objects, data, ids, report_type=None):
        new_ids = ids
        if (data['model'] == 'ir.ui.menu'):
            new_ids = 'chart_account_id' in data['form'] and [data['form']['chart_account_id']] or []
            objects = self.pool.get('account.account').browse(self.cr, self.uid, new_ids)
        return super(report_account_common, self).set_context(objects, data, new_ids, report_type=report_type)

    def _get_multi_names(self, data):
        res = []
        analytic_obj = self.pool.get('account.analytic.account')
        account_obj = self.pool.get('account.account')
        period_obj = self.pool.get('account.period')
        if data.get('form', False):
            if data['form'].get('multiplan', '') == 'analytic':
                res += [a.complete_name for a in analytic_obj.browse(self.cr, self.uid, data['form']['multiplan_analytic_ids'])]
            elif data['form'].get('multiplan', '') == 'financial':
                res += [c.name for c in account_obj.browse(self.cr, self.uid, data['form']['multiplan_financial_ids'])]
            elif data['form'].get('multiplan', '') == 'period':
                res += [c.name for c in period_obj.browse(self.cr, self.uid, data['form']['multiplan_period_ids'])]
        return res

    def get_lines(self, data):
        lines = []
        account_obj = self.pool.get('account.account')
        currency_obj = self.pool.get('res.currency')
        used_context = data['form']['used_context'].copy()
        comparison_context = data['form']['comparison_context'].copy()
        comparison_context['debit_credit'] = used_context['debit_credit'] = data['form'].get('debit_credit')
        ids2 = self.pool.get('account.financial.report')._get_children_by_order(self.cr, self.uid, [data['form']['account_report_id'][0]], context=used_context)
        for report in self.pool.get('account.financial.report').browse(self.cr, self.uid, ids2, context=used_context):
            multiplan = eval(report.multiplan)
            vals = {
                'name': report.name,
                'balance': (sum(multiplan) * report.sign) if multiplan else (report.balance * report.sign),
                'type': 'report',
                'level': bool(report.style_overwrite) and report.style_overwrite or report.level,
                'account_type': report.type =='sum' and 'view' or False, #used to underline the financial report balances
                'multiplan': multiplan and [v and v * report.sign or 0.0 for v in multiplan] or [],
            }
            if data['form']['debit_credit']:
                vals['debit'] = report.debit
                vals['credit'] = report.credit
            if data['form']['enable_filter']:
                vals['balance_cmp'] = self.pool.get('account.financial.report').browse(self.cr, self.uid, report.id, context=comparison_context).balance * report.sign or 0.0
            lines.append(vals)
            account_ids = []
            if report.display_detail == 'no_detail':
                #the rest of the loop is used to display the details of the financial report, so it's not needed here.
                continue
            if report.type == 'accounts' and report.account_ids:
                account_ids = account_obj._get_children_and_consol(self.cr, self.uid, [x.id for x in report.account_ids])
            elif report.type == 'account_type' and report.account_type_ids:
                account_ids = account_obj.search(self.cr, self.uid, [('user_type','in', [x.id for x in report.account_type_ids])])

            multiplan_ids = [0]
            if used_context['multiplan'] == 'financial':
                multiplan_ids = used_context['multiplan_financial_ids']
            elif used_context['multiplan'] == 'analytic':
                multiplan_ids = used_context['multiplan_analytic_ids']
            elif used_context['multiplan'] == 'period':
                multiplan_ids = used_context['multiplan_period_ids']

            if report.type == 'account_type' and report.account_type_ids:
                for report_type in report.account_type_ids:
                    flag = False
                    balance = debit = credit = balance_cmp= 0
                    account_type = 'other'
                    account = False
                    account_vals = []
                    multiplan_vals = multiplan and [0.0 for v in multiplan] or []
                    account_cache = {}
                    for i, multiplan_id in enumerate(multiplan_ids):
                        account_dom = [('user_type', '=', report_type.id)]
                        if used_context['multiplan'] == 'financial':
                            used_context['chart_account_id'] = multiplan_id
                            comparison_context['chart_account_id'] = multiplan_id
                            account_dom += [('id','child_of',multiplan_id)]
                        elif used_context['multiplan'] == 'analytic':
                            used_context['analytic_account_id'] = multiplan_id
                            comparison_context['analytic_account_id'] = multiplan_id
                        elif used_context['multiplan'] == 'period':
                            for ff in ['date_from','date_to']:
                                if used_context.has_key(ff):
                                    del used_context[ff]
                                if comparison_context.has_key(ff):
                                    del comparison_context[ff]
                            used_context['period_from'] = multiplan_id
                            used_context['period_to'] = multiplan_id
                            comparison_context['period_from'] = multiplan_id
                            comparison_context['period_to'] = multiplan_id

                        for account in account_obj.browse(self.cr, self.uid, account_obj.search(self.cr, self.uid, account_dom), context=used_context):
                            balance += account.balance
                            debit += account.debit
                            credit += account.credit
                            account_type = account.type
                            multiplan_val = multiplan and ['' for v in multiplan] or []
                            if multiplan:
                                multiplan_val[i] = account.balance * report.sign
                                multiplan_vals[i] += account.balance * report.sign
                                if account.id in account_cache:
                                    account_vals[account_cache[account.id]]['multiplan'][i] = multiplan_val[i]
                                    account_vals[account_cache[account.id]]['balance'] = sum([v or 0.0 for v in account_vals[account_cache[account.id]]['multiplan']])
                                    continue
                            if data['form']['enable_filter']:
                                balance_cmp += account_obj.browse(self.cr, self.uid, account.id, context=comparison_context).balance
                            if report.display_detail == 'detail_with_hierarchy':
                                account_flag = False
                                account_val = {
                                    'name': account.code + ' ' + account.name,
                                    'balance': account.balance * report.sign,
                                    'type': 'account',
                                    'level': 6,
                                    'account_type': account.type,
                                    'multiplan': multiplan_val,
                                }
                                if data['form']['debit_credit']:
                                    account_val['debit'] = account.debit
                                    account_val['credit'] = account.credit
                                if not currency_obj.is_zero(self.cr, self.uid, account.company_id.currency_id,
                                                            account_val['balance']):
                                    account_flag = True
                                if data['form']['enable_filter']:
                                    account_val['balance_cmp'] = account_obj.browse(self.cr, self.uid, account.id,
                                                                             context=comparison_context).balance * report.sign or 0.0
                                    if not currency_obj.is_zero(self.cr, self.uid, account.company_id.currency_id,
                                                                account_val['balance_cmp']):
                                        account_flag = True
                                if account_flag:
                                    account_vals.append(account_val)
                                    account_cache[account.id] = len(account_vals) - 1
                    vals = {
                        'name': report_type.name,
                        'balance': sum(multiplan_vals) if multiplan else (balance * report.sign),
                        'type': 'account',
                        'level': 6 if report.display_detail == 'detail_flat' else 4,
                        'account_type': account_type,
                        'multiplan': multiplan_vals,
                    }
                    if data['form']['debit_credit']:
                        vals['debit'] = debit
                        vals['credit'] = credit
                    if account and not currency_obj.is_zero(self.cr, self.uid, account.company_id.currency_id, vals['balance']):
                        flag = True
                    if data['form']['enable_filter']:
                        vals['balance_cmp'] = balance_cmp * report.sign or 0.0
                        if account and not currency_obj.is_zero(self.cr, self.uid, account.company_id.currency_id,
                                                    vals['balance_cmp']):
                            flag = True
                    if flag or account_vals:
                        lines.append(vals)
                        lines += account_vals
            elif account_ids:

                for i, multiplan_id in enumerate(multiplan_ids):
                    if used_context['multiplan'] == 'financial':
                        used_context['chart_account_id'] = multiplan_id
                        comparison_context['chart_account_id'] = multiplan_id
                    elif used_context['multiplan'] == 'analytic':
                        used_context['analytic_account_id'] = multiplan_id
                        comparison_context['analytic_account_id'] = multiplan_id

                    for account in account_obj.browse(self.cr, self.uid, account_ids, context=used_context):
                        #if there are accounts to display, we add them to the lines with a level equals to their level in
                        #the COA + 1 (to avoid having them with a too low level that would conflicts with the level of data
                        #financial reports for Assets, liabilities...)
                        if report.display_detail == 'detail_flat' and account.type == 'view':
                            continue
                        flag = False
                        multiplan_val = multiplan and ['' for v in multiplan] or []
                        if multiplan:
                            multiplan_val[i] = account.balance * report.sign
                        vals = {
                            'name': account.code + ' ' + account.name,
                            'balance':  account.balance * report.sign,
                            'type': 'account',
                            'level': report.display_detail == 'detail_with_hierarchy' and min(account.level + 1,6) or 6, #account.level + 1
                            'account_type': account.type,
                            'multiplan': multiplan_val,
                        }

                        if data['form']['debit_credit']:
                            vals['debit'] = account.debit
                            vals['credit'] = account.credit
                        if not currency_obj.is_zero(self.cr, self.uid, account.company_id.currency_id, vals['balance']):
                            flag = True
                        if data['form']['enable_filter']:
                            vals['balance_cmp'] = account_obj.browse(self.cr, self.uid, account.id, context=comparison_context).balance * report.sign or 0.0
                            if not currency_obj.is_zero(self.cr, self.uid, account.company_id.currency_id, vals['balance_cmp']):
                                flag = True
                        if flag:
                            lines.append(vals)
        return lines


class report_financial(osv.AbstractModel):
    _name = 'report.account.report_financial'
    _inherit = 'report.abstract_report'
    _template = 'account.report_financial'
    _wrapped_report_class = report_account_common

class report_financial(osv.AbstractModel):
    _name = 'report.account.report_financial_landscape'
    _inherit = 'report.abstract_report'
    _template = 'account.report_financial_landscape'
    _wrapped_report_class = report_account_common

class report_financial_xls(osv.AbstractModel):
    _name = 'report.account.report_financial_xls'
    _inherit = 'report.abstract_report'
    _template = 'account.report_financial_xls'
    _wrapped_report_class = report_account_common
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
