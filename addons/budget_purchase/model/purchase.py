# -*- coding: utf-8 -*-

from openerp import models, fields, api, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    struct_id = fields.Many2one('budget.struct', 'Budget Struct')

    def _prepare_invoice(self, cr, uid, order, line_ids, context=None):
        """
        :param order:
        :param line_ids:
        :return:
        """
        inv_val = super(PurchaseOrder, self)._prepare_invoice(cr=cr, uid=uid, order=order, line_ids=line_ids, context=context)
        struct = order.struct_id
        if struct:
            inv_val['budget_struct_id'] = struct.id
        return inv_val

