# -*- coding: utf-8 -*-

from openerp import models, fields, api, _


class PurchaseRequisition(models.Model):
    _inherit = "purchase.requisition"

    struct_id = fields.Many2one('budget.struct', string='Budget Struct')

    available = fields.Float(string="Available", compute="compute_available")

    @api.multi
    @api.depends('struct_id', 'account_analytic_id')
    def compute_available(self):
        return 0.0
