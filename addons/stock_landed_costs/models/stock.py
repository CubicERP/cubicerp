# -*- coding: utf-8 -*-
##############################################################################
#
#    Cubic ERP, Enterprise and Government Management Software
#    Copyright (C) 2020 Cubic ERP & Teradata SAC (<http://cubicerp.com>).
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

from odoo import fields, models, exceptions, _


class StockPicking(models.Model):
    _inherit = "stock.picking"

    landed_cost_ids = fields.Many2many("stock.landed.cost", 'stock_landed_cost_stock_picking_rel', 'stock_picking_id', 'stock_landed_cost_id')

    def action_done(self):
        res = super(StockPicking, self).action_done()
        costs = self.mapped('move_lines').mapped('purchase_line_id').mapped('order_id').mapped('landed_cost_id')
        if costs:
            costs[0].picking_ids |= self
        return res

    def action_cancel(self):
        res = super(StockPicking, self).action_cancel()
        if self.mapped('landed_cost_ids').filtered(lambda c: c.state != 'draft'):
            raise exceptions.ValidationError(_("The landed cost %s must be in draft state")%(', '.join([c.name for c in self.mapped('landed_cost_ids').filtered(lambda c: c.state != 'draft')])))
        for cost in self.mapped('landed_cost_ids'):
            cost.landed_cost_ids = cost.landed_cost_ids - self
        return res


class StockMove(models.Model):
    _inherit = "stock.move"

    landed_cost_ids = fields.Many2many("stock.landed.cost", 'stock_landed_cost_stock_move_rel', 'move_id', 'cost_id')
    landed_cost_id = fields.Many2one("stock.landed.cost", help="Technical field for landed cost in post state")

    def _fifo_write(self, candidate_vals, move):
        candidate = self
        if candidate.landed_cost_id:
            candidate.landed_cost_id.stock_move_ids |= move
        return super(StockMove, self)._fifo_write(candidate_vals, move)

    def _action_cancel(self):
        res = super(StockMove, self)._action_cancel()
        for cost in self.mapped('landed_cost_ids'):
            cost.stock_move_ids = cost.stock_move_ids - self
        return res