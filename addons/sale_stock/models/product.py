# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE_LGPL file for full copyright and licensing details.

from odoo import fields, models, exceptions, _
from odoo.tools import float_compare


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def stock_message(self, product_uom_qty, product_uom, warehouse_id, route_id=False, lang=False):
        self.ensure_one()
        warning_mess = {}
        if self.type == 'product':
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            product = self.with_context(
                warehouse=warehouse_id.id,
                lang=lang or self.env.user.lang or 'en_US'
            )
            product_qty = product_uom._compute_quantity(product_uom_qty, self.uom_id)
            if float_compare(product.virtual_available, product_qty, precision_digits=precision) == -1:
                is_available = self._check_routing(warehouse_id, route_id)
                if not is_available and self._context.get('warning-available-stock',True):
                    message =  _('You plan to sell %s %s but you only have %s %s available in %s warehouse.') % \
                            (product_uom_qty, product_uom.name, product.virtual_available, product.uom_id.name, warehouse_id.name)
                    # We check if some products are available in other warehouses.
                    if float_compare(product.virtual_available, self.virtual_available, precision_digits=precision) == -1:
                        message += _('\nThere are %s %s available accross all warehouses.') % \
                                (self.virtual_available, product.uom_id.name)
                    for warehouse in self.env['stock.warehouse'].search([('id','!=',warehouse_id.id)]):
                        product = self.with_context(warehouse=warehouse.id,
                                                               lang=lang or self.env.user.lang or 'en_US')
                        message += _('\n - %s : %s %s') % (warehouse.name, product.virtual_available, product.uom_id.name)
                    warning_mess = {
                        'title': _('Not enough inventory!'),
                        'message' : message
                    }
        return warning_mess

    def _check_routing(self, warehouse_id, route_id=False):
        """ Verify the route of the product based on the warehouse
            return True if the product availibility in stock does not need to be verified,
            which is the case in MTO, Cross-Dock or Drop-Shipping
        """
        is_available = False
        product_routes = route_id or (self.route_ids + self.categ_id.total_route_ids)
        # Check MTO
        wh_mto_route = warehouse_id.mto_pull_id.route_id
        if wh_mto_route and wh_mto_route <= product_routes:
            is_available = True
        else:
            mto_route = False
            try:
                mto_route = self.env['stock.warehouse']._get_mto_route()
            except exceptions.UserError:
                # if route MTO not found in ir_model_data, we treat the product as in MTS
                pass
            if mto_route and mto_route in product_routes:
                is_available = True
        # Check Drop-Shipping
        if not is_available:
            for pull_rule in product_routes.mapped('pull_ids'):
                if pull_rule.picking_type_id.sudo().default_location_src_id.usage == 'supplier' and\
                        pull_rule.picking_type_id.sudo().default_location_dest_id.usage == 'customer':
                    is_available = True
                    break
        return is_available