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

from odoo import fields, models, _, api


class StockImmediateTransfer(models.TransientModel):
    _name = 'stock.quick.transfer'
    _description = 'Quick Transfer'

    location_id = fields.Many2one("stock.location", "Source Location", required=True)
    location_dest_id = fields.Many2one("stock.location", "Destination Location", required=True)
    origin = fields.Char("Source Document")
    picking_type_id = fields.Many2one("stock.picking.type", "Operation Type", required=True)
    product_id = fields.Many2one("product.product", required=True)
    product_uom_id = fields.Many2one("product.uom", related="product_id.uom_id", readonly=True)
    lot_id = fields.Many2one('stock.production.lot', 'Lot/Serial Number')
    package_id = fields.Many2one('stock.quant.package', 'Destinity Package')
    quantity_done = fields.Float("Quantity")

    def process(self):
        quant = self.env['stock.quant'].browse(self._context.get('active_ids')[0])

        vals = self.env['stock.picking'].default_get(list(self.env['stock.picking']._fields.keys()))
        vals.update({
            'location_id': self.location_id.id,
            'location_dest_id': self.location_dest_id.id,
            'origin': self.origin,
            'picking_type_id': self.picking_type_id.id,
            'move_lines': [(0, False, {
                'name': quant.product_id.name,
                'product_id': quant.product_id.id,
                'product_uom': quant.product_id.uom_id.id,
                'product_uom_qty': self.quantity_done,
                'quantity_done': self.quantity_done,
            })]
        })
        picking = self.env['stock.picking'].create(vals)
        picking.move_lines.move_line_ids.write({
            'lot_id': quant.lot_id.id,
            'package_id': quant.package_id.id,
            'result_package_id': self.package_id.id,
        })
        picking.button_validate()
        return picking.id

    @api.onchange("picking_type_id", "location_dest_id")
    def onchange_picking_type(self):
        if self.picking_type_id:
            self.location_dest_id = self.picking_type_id.default_location_dest_id
            return {'domain': {'package_id': ['|',('location_id', '=', False),('location_id', '=', self.location_dest_id.id)]}}
