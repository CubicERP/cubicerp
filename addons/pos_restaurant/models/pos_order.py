# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE_LGPL file for full copyright and licensing details.

from odoo import api, fields, models


class PosOrder(models.Model):
    _inherit = 'pos.order'

    table_id = fields.Many2one('restaurant.table', string='Table', help='The table where this order was served')
    customer_count = fields.Integer(string='Guests', help='The amount of customers that have been served by this order.')

    @api.model
    def _order_fields(self, ui_order):
        order_fields = super(PosOrder, self)._order_fields(ui_order)
        order_fields['table_id'] = ui_order.get('table_id', False)
        order_fields['customer_count'] = ui_order.get('customer_count', 0)
        if self.env['pos.session'].browse(ui_order['pos_session_id']).config_id.iface_notes_print:
            notes = ""
            for line in ui_order['lines']:
                if line[2].get('note'):
                    notes += "- %s: %s\n"%(self.env['product.product'].browse(line[2].get('product_id')).name, line[2].get('note'))
                if 'note' in line[2]:
                    line[2].pop('note')
                if 'mp_skip' in line[2]:
                    line[2].pop('mp_skip')
                if 'mp_dirty' in line[2]:
                    line[2].pop('mp_dirty')
            if notes:
                order_fields['note'] = notes
        return order_fields