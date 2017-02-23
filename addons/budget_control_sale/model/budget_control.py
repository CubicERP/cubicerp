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

from openerp import models, api, fields, _


class BudgetMove(models.Model):
    _inherit = "budget.move"

    sale_id = fields.Many2one('sale.order', string="Sale Order", states={'draft': [('readonly', False)]}, readonly=True)

    def _create_move_values(self, line=None, purchase=None, sale=None):
        res = super(BudgetMove, self)._create_move_values(line=line, purchase=purchase, sale=sale)
        if sale:
            res['sale_id'] = sale.id
            if not res.get('period_id', False) and sale.date_order:
                periods = self.env['budget.period'].find(dt=sale.date_order)
                res['period_id'] = periods and periods[0].id or False
            if sale.date_order:
                res['date'] = sale.date_order
            res['ref'] = sale.name
        return res

    def create_from_so(self, sale):
        move = self.create(self._create_move_values(sale=sale))
        for line_dict in self._create_lines_values(move, sale=sale):
            self.env['budget.move.line'].create(line_dict)
        return move

