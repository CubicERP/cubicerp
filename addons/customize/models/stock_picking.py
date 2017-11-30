# -*- encoding: utf-8 -*-
##############################################################################
#
#    Branch Cubic ERP, Enterprise Management Software
#    Copyright (C) 2013 Cubic ERP - Teradata SAC (<http://cubicerp.com>).
#
#    This program can only be used with a valid Branch Cubic ERP agreement,
#    it is forbidden to publish, distribute, modify, sublicense or sell 
#    copies of the program.
#
#    The adove copyright notice must be included in all copies or 
#    substancial portions of the program.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT WARRANTY OF ANY KIND; without even the implied warranty
#    of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
##############################################################################

from openerp import models, fields, api

class stock_picking(models.Model):
    _inherit = 'stock.picking'
    
    voucher_type=fields.Char(string='Voucher type', compute='_get_voucher_type')
    voucher_number=fields.Char(string='Voucher number', compute='_get_voucher')

    @api.one
    @api.multi
    @api.depends('sale_id')
    def _get_voucher(self):
        res=''
        for invoice in self.sale_id.invoice_ids:
            res += str(invoice.number) + ' / '
        if res[-3:] == ' / ': 
            res = res[:-3]
        self.voucher_number= res

    @api.one
    @api.multi
    @api.depends('sale_id')    
    def _get_voucher_type(self):
        res=''
        for invoice in self.sale_id.invoice_ids:
            res += str(invoice.journal_id.name) + ' / '
        if res[-3:] == ' / ': 
            res = res[:-3]
        self.voucher_type= res


    
    
    
