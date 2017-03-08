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

from openerp.osv import osv
from openerp.tools.translate import _


class PurchaseLineInvoice(osv.osv_memory):
    """ To create invoice for purchase order line"""

    _inherit = 'purchase.order.line_invoice'
    _description = 'Purchase Order Line Make Invoice'

    def _make_invoice_by_partner(self, cr, uid, partner, orders, lines_ids, context=None):
        invoice_id = super(PurchaseLineInvoice, self)._make_invoice_by_partner(cr=cr, uid=uid, partner=partner,
                                                                               orders=orders,
                                                                               lines_ids=lines_ids, context=context)
        struct = orders[0].struct_id
        if struct:
            self.pool.get('account.invoice').write(cr, uid, [invoice_id], {'budget_struct_id': struct.id}, context=context)
        return invoice_id

    def makeInvoices(self, cr, uid, ids, context=None):

        """
             To get Purchase Order line and create Invoice
             @param self: The object pointer.
             @param cr: A database cursor
             @param uid: ID of the user currently logged in
             @param context: A standard dictionary
             @return : retrun view of Invoice
        """

        order_lines_2invoice_ids = context.get('active_ids', [])

        if order_lines_2invoice_ids:

            purchase_line_obj = self.pool.get('purchase.order.line')

            order_lines_2invoice = purchase_line_obj.browse(cr, uid, order_lines_2invoice_ids, context=context)
            structs = order_lines_2invoice.mapped('order_id.struct_id')

            if not structs:
                return super(PurchaseLineInvoice, self).makeInvoices(cr=cr, uid=uid, ids=ids, context=context)
            else:
                res = False
                invoices = {}
                purchase_obj = self.pool.get('purchase.order')
                invoice_line_obj = self.pool.get('account.invoice.line')

                for order_line in order_lines_2invoice:
                    if (not order_line.invoiced) and (order_line.state not in ('draft', 'cancel')):
                        if not (order_line.partner_id.id, order_line.order_id.struct_id) in invoices:
                            invoices[order_line.partner_id.id, order_line.order_id.struct_id.id] = []
                        acc_id = purchase_obj._choose_account_from_po_line(cr, uid, order_line, context=context)
                        inv_line_data = purchase_obj._prepare_inv_line(cr, uid, acc_id, order_line, context=context)
                        inv_line_data.update({'origin': order_line.order_id.name})
                        inv_id = invoice_line_obj.create(cr, uid, inv_line_data, context=context)
                        purchase_line_obj.write(cr, uid, [order_line.id],
                                                {'invoiced': True, 'invoice_lines': [(4, inv_id)]})
                        invoices[order_line.partner_id.id, order_line.order_id.struct_id.id].append(
                            (order_line, inv_id))

                res = []
                for result in invoices.values():
                    il = map(lambda x: x[1], result)
                    orders = list(set(map(lambda x: x[0].order_id, result)))

                    res.append(
                        self._make_invoice_by_partner(cr, uid, orders[0].partner_id, orders, il, context=context))

                return {
                    'domain': "[('id','in', [" + ','.join(map(str, res)) + "])]",
                    'name': _('Supplier Invoices'),
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'res_model': 'account.invoice',
                    'view_id': False,
                    'context': "{'type':'in_invoice', 'journal_type': 'purchase'}",
                    'type': 'ir.actions.act_window'
                }
        else:
            return super(PurchaseLineInvoice, self).makeInvoices(cr=cr, uid=uid, ids=ids, context=context)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
