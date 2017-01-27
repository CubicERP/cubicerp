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

    budget_period_id = fields.Many2one('budget.period', string='Budget Period')
    type = fields.Selection([('normal', 'Normal'),
                             ('view', 'View')], string="Type", default='normal')

    @api.multi
    def _get_structs(self):
        """Return default Period value"""
        # find all budget lines with this period
        # get the struct of this lines
        domain, budget_line_obj, structs = [], self.env['budget.budget.lines'], None
        for chart in self:
            if chart.budget_period_id:
                domain.extend([('budget_period_id', '=', chart.budget_period_id.id)])
            structs = budget_line_obj.search(domain).mapped('struct_budget_id')
            if chart.type:
                structs.filtered(lambda struct: struct.type == chart.type)
        return structs

    @api.multi
    def struct_chart_open_window(self):
        """
        Opens chart of Accounts
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of account chart’s IDs
        @return: dictionary of Open account chart window on given fiscalyear and all Entries or posted entries
        """
        model_data_obj = self.env['ir.model.data']
        action_obj = self.env['ir.actions.act_window']
        if not self._context:
            self._context = {}
        data = self.read([])[0]
        result = model_data_obj.get_object_reference('budget', 'budget_struct_tree_action')
        id = result and result[1] or False  # xml_id
        result = action_obj.browse([id]).read([])[0]
        result['domain'] = str([('id', 'in', self._get_structs().ids)])
        return result

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
