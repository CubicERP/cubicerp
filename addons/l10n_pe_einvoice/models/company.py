# -*- encoding: utf-8 -*-
##############################################################################
#
#    Branch Cubic ERP, Enterprise Management Software
#    Copyright (C) 2016 Cubic ERP - Teradata SAC (<http://cubicerp.com>).
#
#    This program can only be used with a valid Branch Cubic ERP agreement,
#    it is forbidden to publish, distribute, modify, sublicense or sell
#    copies of the program.
#
#    The above copyright notice must be included in all copies or
#    substantial portions of the program.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT WARRANTY OF ANY KIND; without even the implied warranty
#    of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
##############################################################################

from openerp.osv import osv, fields

class res_company(osv.Model):
    _inherit = 'res.company'
    
    _columns = {
            'sunat_certificate': fields.many2one('pki.certificate', string="Sunat Certificate",
                                                 domain=[('state','=','done')]),
            'sunat_see_server': fields.many2one('einvoice.server', string="Sunat SEE Server",
                                                domain=[('state','=','ready')]),
            'sunat_see_online': fields.boolean('eInvoice is Online'),
            'comercial_name': fields.char('Comercial Name'),
            'resolution_number': fields.char('Resolution Number'),
            'resolution_type': fields.char('Resolution type'),
            
        }
    
    _defaults = {
            'sunat_see_online': True,
        }