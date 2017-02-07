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


# class StructControlChart(models.Model):
#     """
#     For Chart of Struct
#     """
#     _name = "budget.struct.control.chart"
#     _description = "Struct Control Chart"
#
#     struct_id = fields.Many2one('budget.struct', string='Budget Struct')
#     company_id = fields.Many2one('res.company', string='Company')
#     period_id = fields.Many2one('budget.period', string='Budget Period')
#     analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account')
#
#     @api.multi
#     def struct_chart_open_window(self):
#         """
#         Opens chart of Accounts
#         @param cr: the current row, from the database cursor,
#         @param uid: the current user’s ID for security checks,
#         @param ids: List of account chart’s IDs
#         @return:
#         """
#
#         ACT_WINDOW_MAP = {
#             'budget.lines': ('action1', 'action1.1'),
#             'control.lines': ('action2', 'action2.1'),
#             }
#
#
#         (act_hierch_view, btn_click_act) = ACT_WINDOW_MAP[self._context.get('show_info')]
#
#         result = self.env.ref('budget_control.budget_struct_control_hierarchy_tree_action2').read()[0]
#         domain = [('parent_id', '=', False)]
#         if self.struct_id:
#             domain = [('parent_id', '=', self.struct_id.id)]
#
#         result['context'] = str({'move_action': 'budget_move_lines_tree_view_action'})
#         result['domain'] = str(domain)
#         return result
#
#         self.ensure_one()
#         result = self.env.ref('budget_control.budget_struct_control_hierarchy_tree_action2').read()[0]
#         domain = [('parent_id', '=', False)]
#         if self.struct_id:
#             domain = [('parent_id', '=', self.struct_id.id)]
#
#         result['context'] = str({'move_action': 'budget_move_lines_tree_view_action'})
#         result['domain'] = str(domain)
#         return result


class StructChart(models.Model):
    """
    For Chart of Struct
    """
    _inherit = "budget.struct.chart"

    @api.model
    def _get_tree_but_open_action(self):
        if self._context.get('src_wizard_act'):
            return self.env.ref('budget_control.budget_move_lines_tree_view_action')

        return super(StructChart, self)._get_tree_but_open_action()

    @api.model
    def _get_hierarchy_action(self):
        if self._context.get('src_wizard_act'):
            return self.env.ref('budget_control.budget_struct_control_hierarchy_tree_action2')

        return super(StructChart, self)._get_hierarchy_action()


    @api.multi
    def struct_chart_open_window(self):
        """
        Opens chart of Accounts
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of account chart’s IDs
        @return:
        """
        res = super(StructChart, self).struct_chart_open_window()

        action_id = self._get_tree_but_open_action()

        res['context'] = str({
            'show_amounts': True,
            'action_id': action_id.id,
            'company_id': self.company_id.id or None,
            'period_id': self.budget_period_id.id or None,
            'analytic_id': self.analytic_acc_id.id or None,
            })
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
