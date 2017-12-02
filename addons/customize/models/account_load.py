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

class account_load_move(osv.Model):
    _name = "account.load.move"
    _inherit = "account.load.move"

    def create(self, cr, uid, values, context=None):
        if values.get('currency_amount',0) and not values.has_key('currency_id'):
            load = self.pool.get('account.load').browse(cr, uid, values['load_id'], context=context)
            journal = self.pool.get('account.journal').browse(cr, uid, values['journal_id'], context=context)
            if journal.type in ('bank','cash') and not journal.currency:
                values['currency_amount'] = 0.0
            values['currency_id'] = load.company_id.currency2_id.id
        return super(account_load_move, self).create(cr, uid, values, context=context)
