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

from odoo import api, models, _
from odoo.tools import float_repr
import json


rec = 0
def autoIncrement():
    global rec
    pStart = 1
    pInterval = 1
    if rec == 0:
        rec = pStart
    else:
        rec += pInterval
    return rec


class AccountReportLedger(models.TransientModel):
    _name = 'account.report.ledger'

    def convert_lines(self, data, model=False, model_id=0, parent_id=None, level=1):
        res = []
        company = self._context.get('company_id') and self.env['res.company'].browse(self._context.get('company_id')[0]) or self.env.user.company_id
        if model and model_id:
            for d in data:
                for m in d['move_lines']:
                    r = {'id': autoIncrement(),
                         'model': model,
                         'model_id': model_id,
                         'unfoldable': False,
                         'parent_id': parent_id,
                         'level': level,
                         'type': 'line',
                         'res_model': 'account.move.line',
                         'res_id': m['lid'],
                         'reference': m['move_name'],
                         'columns': [m['move_name'],
                                     m['ldate'],
                                     m['lcode'],
                                     m['partner_name'],
                                     "%s%s" % (m['lname'], m.get('lref') and " - %s" % m['lref'] or ''),
                                     m['debit'],
                                     m['credit'],
                                     m['balance'],
                                     m['amount_currency'] and "%s %s"%(m['currency_code'],float_repr(m['amount_currency'],company.currency_id.decimal_places)) or company.currency_id.symbol,
                                     ]
                         }
                    res.append(r)
        else:
            total = [(_('Undistributed profit'),"white-space: nowrap;text-align: right;font-weight: normal;font-style: italic;"),0.0,0.0,0.0,company.currency_id.symbol or '']
            for d in data:
                r = {'id': autoIncrement(),
                     'model': model or 'account.account',
                     'model_id': model_id or d.get('account_id'),
                     'unfoldable': False if model else bool(d.get('move_lines')),
                     'parent_id': parent_id,
                     'level': level,
                     'type': 'line',
                     'columns' : ["%s %s"%(d['code'],d['name']),
                                  d['debit'],
                                  d['credit'],
                                  d['balance'],
                                  company.currency_id.symbol or '',
                                  ]
                     }
                res.append(r)
                total[3] += d['balance']
            if total[3]:
                total[1] = (float_repr(total[3] > 0.0 and total[3] or 0.0, company.currency_id.decimal_places),"white-space: nowrap;text-align: right;font-weight: normal;font-style: italic;")
                total[2] = (float_repr(total[3] < 0.0 and (-1.0 * total[3]) or 0.0, company.currency_id.decimal_places),"white-space: nowrap;text-align: right;font-weight: normal;font-style: italic;")
                total[3] = (float_repr(total[3], company.currency_id.decimal_places),"white-space: nowrap;text-align: right;font-weight: normal;font-style: italic;")
                res.append({
                    'id': autoIncrement(),
                    'model': model or 'account.account',
                    'model_id': 0,
                    'unfoldable': False,
                    'parent_id': 0,
                    'level': level,
                    'type': 'line',
                    'columns': total,
                })
        return res

    @api.model
    def get_lines(self, line_id=None, **kw):
        form = dict(self.env.context)
        model = False
        model_id = False
        level = 1
        if kw:
            level = kw['level']
            model = kw['model_name']
            model_id = kw['model_id']
            form = kw['form']

        accounts = self.env['account.account'].browse(model_id) if model == 'account.account' else self.env['account.account'].search([])
        res = self.env['report.account.report_generalledger'].with_context(form.get('used_context', {}))._get_account_move_entry(accounts,
                                                                                                       form.get('initial_balance'),
                                                                                                       form.get('sortby'),
                                                                                                       form.get('display_account'))
        return self.convert_lines(res, model=model, model_id=model_id, parent_id=line_id, level=level)

    def _get_html(self):
        result = {}
        rcontext = {}
        form = dict(self.env.context)
        company = form.get('company_id') and self.env['res.company'].browse(form.get('company_id')[0]) or self.env.user.company_id
        rcontext['lines'] = self.with_context(form).get_lines()
        rcontext['print_journal'] = [j.code for j in self.env['account.journal'].browse(form.get('journal_ids',[]))]
        rcontext['company'] = company.name
        form['decimal_places'] = company.currency_id.decimal_places
        form['report_name'] = 'account.report_generalledger'
        form['active_model'] = 'account.report.general.ledger'
        form['active_id'] = self.env.ref('account.action_report_general_ledger').id
        rcontext['data'] = form
        rcontext['form'] = json.dumps(form)
        result['html'] = self.env.ref('account_report.report_account_ledger').render(rcontext)
        return result

    @api.model
    def get_html(self, data=None):
        res = self.search([('create_uid', '=', self.env.uid)], limit=1)
        if not res:
            return self.create({}).with_context(data.get('form',{}))._get_html()
        return res.with_context(data.get('form',{}))._get_html()
