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

class account_journal(osv.Model):
    _inherit = 'account.journal'
    
    def _get_type(self, cr, uid, context=None):
        return self.pool.get('base.element').get_as_selection(cr, uid, 'PE.SEE.TIPO', context=context)
    
    _columns = {
            'is_einvoice_pe': fields.boolean('Peruvian Electronic Invoice'),
            'batch_type_pe': fields.selection(_get_type, string="eInvoice Type"),
            'is_synchronous': fields.boolean('Is synchronous'),
        }
    _defaults = {
            'is_einvoice_pe': False,
            'is_synchronous': False,
        }
    

class account_tax(osv.Model):
    _inherit = 'account.tax'
    
    def _get_igv_type(self, cr, uid, context=None):
        return self.pool.get('base.element').get_as_selection(cr, uid, 'PE.SEE.CATALOGO_07', context=context)
    
    def _get_price_type(self, cr, uid, context=None):
        return self.pool.get('base.element').get_as_selection(cr, uid, 'PE.SEE.CATALOGO_16', context=context)
    
    _columns = {
            'igv_type_pe': fields.selection(_get_igv_type, string="eInvoice IGV Type"),
            'price_type_pe': fields.selection(_get_price_type, string="eInvoice Price Type"),
        }

class account_tax_code(osv.Model):
    _inherit = 'account.tax.code'
    
    def _get_igv_type(self, cr, uid, context=None):
        return self.pool.get('base.element').get_as_selection(cr, uid, 'PE.SEE.CATALOGO_07', context=context)
    
    def _get_other_tax_type(self, cr, uid, context=None):
        return self.pool.get('base.element').get_as_selection(cr, uid, 'PE.SEE.CATALOGO_14', context=context)
    
    _columns = {
            'tax_type_pe': fields.many2one('base.element', 'eInvoice Tax Type', domain=[('table_id.code','=','PE.SEE.CATALOGO_05')]),
            'igv_type_pe': fields.selection(_get_igv_type, string="eInvoice IGV Type"),
            'other_tax_type_pe': fields.selection(_get_other_tax_type, string="Other eInvoice Tax Type"),
        }