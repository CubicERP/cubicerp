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

from openerp import models, fields, api, _


class StructChart(models.Model):
    """
    For Chart of Struct
    """
    _name = "budget.struct.chart"
    _description = "Struct Chart"

    struct_parent_id = fields.Many2one('budget.struct', string='Budget Struct', required=True)
    company_id = fields.Many2one('res.company', string='Company')
    budget_period_id = fields.Many2one('budget.period', string='Budget Period')
    analytic_acc_id = fields.Many2one('account.analytic.account', string='Analytic Account')

    @api.multi
    def _get_structs(self, budget_parent=None, analytic_acc=None, period=None, company=None):
        """Return default Period value"""
        # find all budget lines with this period
        # get the struct of this lines
        self.ensure_one()
        domain, lines_obj, structs = [], self.env['budget.budget.lines'], None
        for chart in self:
            if chart.budget_period_id:
                domain.extend([('budget_period_id', '=', chart.budget_period_id.id)])
            if chart.struct_parent_id:
                struct_ids = chart.struct_parent_id | chart.struct_parent_id.full_child_ids
                domain.extend([('struct_budget_id', 'in', struct_ids.ids)])
            if chart.analytic_acc_id:
                analytic_ids = chart.analytic_acc_id | chart.analytic_acc_id.child_complete_ids
                domain.extend([('analytic_account_id', 'in', analytic_ids.ids)])
            if chart.company_id:
                domain.extend([('company_id', '=', chart.company_id.id)])

        return lines_obj.search(domain).mapped('struct_budget_id')

    @api.multi
    def struct_chart_open_window(self):
        """
        Opens chart of Accounts
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of account chart’s IDs
        @return:
        """
        self.ensure_one()

        result = self.env.ref('budget.open_budget_struct').read()[0]

        result['context'] = str({'group_by': 'parent_id', 'show_amounts': True})
        result['domain'] = str([('id', 'in', self._get_structs().ids)])
        result['flags'] = {'search_view': False}
        return result

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
