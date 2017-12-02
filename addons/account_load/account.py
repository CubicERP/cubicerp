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

from osv import osv, fields


class account_journal(osv.osv):
    _inherit = 'account.journal'
    _columns = {
            'load_account_id': fields.many2one('account.account', 'Load Account', 
                                               help="Used to complete the double entry on initial account load move"),
        }

# class account_move(osv.Model):
#     
#     _name = 'account.move'
#     _inherit = 'account.move'
#     _columns = {
#             'expense_id': fields.many2one('account.expense', string='Account Expense'),
#         }
