# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE_LGPL file for full copyright and licensing details.

from odoo import api, exceptions, fields, models, _


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    use_next_on_work_order_id = fields.Many2one('mrp.workorder',
        help='Technical: used to figure out default serial number on work orders')
