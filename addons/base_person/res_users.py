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
from openerp.tools.translate import _

class res_users(osv.osv):
    _name = 'res.users'
    _inherit = 'res.users'
    
    def onchange_person_name(self, cr, uid, ids, first_name, middle_name, surname, mother_name, context=None):
        res = {'value':{}}
        res['value']['name'] = (first_name and (first_name+' ') or '') + (middle_name and (middle_name+' ') or '') + (surname and (surname+' ') or '') + (mother_name and (mother_name+' ') or '')
        return res

res_users()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
