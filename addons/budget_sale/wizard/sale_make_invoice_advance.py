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


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    def _prepare_advance_invoice_vals(self, cr, uid, ids, context=None):
        sale_obj, sale = self.pool.get('sale.order'), None
        res = super(SaleAdvancePaymentInv, self)._prepare_advance_invoice_vals(cr=cr, uid=uid, ids=ids, context=context)
        sale_id, inv_val = res[0]
        if sale_id:
            sale = sale_obj.browse(cr, uid, [sale_id], context=context)
        if sale.struct_id and inv_val and 'budget_struct_id' not in inv_val.keys():
            inv_val['budget_struct_id'] = sale.struct_id.id
        return res

    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
