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

class res_partner(osv.Model):
    _inherit = 'res.partner'
    _columns = {
        'pe_4ta_suspension_id': fields.many2one('l10n_pe_4ta.suspension', string="Suspension 4th Category",
                                                help="This field contains the suspension certificate for retentions of rents 4th category"),
        }
