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
# from openerp.osv import fields, osv
from openerp import models, fields, api, _


class AccountBudgetCrossveredSummaryReport(models.Model):
    """
    This wizard provides the crossovered budget summary report'
    """
    _name = 'account.budget.crossvered.summary.report'
    _description = 'Account Budget  crossvered summary report'

    date_from = fields.Date(string='Start of period', required=True, default=lambda self: self._default_date_from)
    date_to = fields.Date(string='End of period', required=True, default=lambda self: self._default_date_to)

    def _default_date_from(self):
        return lambda *a: time.strftime('%Y-01-01')

    def _default_date_to(self):
        return lambda *a: time.strftime('%Y-%m-%d')

    @api.multi
    def check_report(self):
        ctx = self._context
        if ctx is None:
            ctx = {}
        data = self.read()[0]
        datas = {
            'ids': ctx.get('active_ids', []),
            'model': 'crossovered.budget',
            'form': data
        }
        datas['form']['ids'] = datas['ids']
        datas['form']['report'] = 'analytic-one'
        return self.pool['report'].get_action([], 'account_budget.report_crossoveredbudget', data=datas)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
