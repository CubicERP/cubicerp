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

from openerp import models, api, fields, _


class SaleOrder(models.Model):
    _inherit = "sale.order"

    struct_id = fields.Many2one('budget.struct', string="Budget Struct", readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})

    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        inv_val = super(SaleOrder, self)._prepare_invoice(cr=cr, uid=uid, order=order, lines=lines, context=context)
        if order.struct_id:
            inv_val['budget_struct_id'] = order.struct_id.id
        return inv_val


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
