# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Cubic ERP (<http://cubicerp.com>).
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

from openerp.osv import fields, osv

class stock_picking(osv.osv):
    _name = 'stock.picking'
    _inherit = 'stock.picking'

    _columns = {
        'landed_costs_ids': fields.many2many('stock.landed.cost', string='Landed Costs', readonly=True, copy=False),
    }

# class stock_move(models.Model):
#     _name = 'stock.move'
#     _inherit = 'stock.move'
#     
#     def _price_unit_user_currency(self, cr, uid, ids, field_name, args, context=None):
#         if context is None:
#             context = {}
#         currency_obj = self.pool.get('res.currency')
#         res = {}
#         local_context = context.copy()
#         for move in self.browse(cr, uid, ids, context=context):
#             local_context['date'] = move.date
#             res[move.id] = currency_obj.compute(cr, uid, move.currency_id.id, move.company_id.currency_id.id, move.price_unit, context=local_context)
#         return res
#     
#     _columns = {    
#             'price_unit_user_currency': fields.function(_price_unit_user_currency, type='float', string='Price Unit', readonly=True,
#                                                       help='Price unit in company currency.'),
#         }
    