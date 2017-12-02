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

from openerp.osv import osv, fields
import openerp.addons.decimal_precision as dp

class account_voucher(osv.Model):
    _name = "account.voucher"
    _inherit = "account.voucher"
    
    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        if context is None: context = {}
        res = []
        for voucher in self.browse(cr, uid, ids, context=context):
            name = ''
            if voucher.number:
                name += '['+voucher.number
            if voucher.reference:
                if name:
                    name += ' / '+voucher.reference + '] '
                else:
                    name += '['+voucher.reference+'] '
            elif name:
                name += '] '
            if voucher.partner_id:
                name += voucher.partner_id.name + ' '
            name += "(%s %.2f)"%(voucher.currency_id.symbol, voucher.amount)
            res.append((voucher.id,name))
        return res
