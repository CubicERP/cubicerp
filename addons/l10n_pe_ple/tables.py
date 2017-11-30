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

class account_account(osv.Model):
    _inherit = "account.account"
    
    _columns = {
        'bank_account_id': fields.many2one("res.partner.bank", "Related bank account", on_delete="restrict"),
    }

class journal(osv.Model):
    _inherit = "account.journal"
    
    def _get_payment_code_selection (self, cr, uid, context=None):
        return self.pool.get('base.element').get_as_selection(cr, uid, 'PE.SUNAT.TABLA_01', context=context)
    
    def _get_payment_type_selection (self, cr, uid, context=None):
        return self.pool.get('base.element').get_as_selection(cr, uid, 'PE.SUNAT.TABLA_10', context=context)
    
    def _get_customs_code_selection (self, cr, uid, context=None):
        return self.pool.get('base.element').get_as_selection(cr, uid, 'PE.SUNAT.TABLA_11', context=context)
    
    def _get_operation_type_selection (self, cr, uid, context=None):
        return self.pool.get('base.element').get_as_selection(cr, uid, 'PE.SUNAT.TABLA_12', context=context)
    
    def _get_revenue_kind_selection (self, cr, uid, context=None):
        return self.pool.get('base.element').get_as_selection(cr, uid, 'PE.SUNAT.TABLA_31', context=context)
    
    _columns = {
        'sunat_payment_code': fields.selection(_get_payment_code_selection, "Payment type", 
                                               help="Medio de pago, according to SUNAT Table 01"),
        'sunat_payment_type': fields.selection(_get_payment_type_selection, "Document type", 
                                               help="Tipo de comprobante de pago o documento, according to SUNAT Table 10"),    
        'sunat_customs_code': fields.selection(_get_customs_code_selection, "Customs code", 
                                               help="Código de aduana, according to SUNAT Table 11"),    
        'sunat_operation_type': fields.selection(_get_operation_type_selection, "Operation type", 
                                                 help="Tipo de operación, according to SUNAT Table 12"), 
        'sunat_revenue_kind': fields.selection(_get_revenue_kind_selection, "Tipo de Renta", 
                                               help="Tipo de Renta de acuerdo a la tabla 31"),   
    }

class account_invoice(osv.Model):
    _inherit = "account.invoice"

    def _get_exoneration_selection (self, cr, uid, context=None):
        return self.pool.get('base.element').get_as_selection(cr, uid, 'PE.SUNAT.TABLA_33', context=context)
    
    def _get_kind_service_selection (self, cr, uid, context=None):
        return self.pool.get('base.element').get_as_selection(cr, uid, 'PE.SUNAT.TABLA_32', context=context)
    
    _columns = {
        'sunat_exoneration': fields.selection(_get_exoneration_selection, "Exoneración Aplicada", 
                                               help="Exoneración Aplicada de acuerdo a la tabla 33"),
        
        'sunat_kind_service': fields.selection(_get_kind_service_selection, "Tipo de Servicio", 
                                               help="Modalidad del servicio prestado por el no domiciliado, según tabla 32"),
        'sunat_lir_art_76': fields.boolean("Sujeto al Art 76 LIR", help="Aplicación del penúltimo párrafo del Art. 76° de la Ley del Impuesto a la Renta"),
    }

# class account_move(osv.Model):
#     _inherit = "account.move"
#
#     def _get_payment_code_selection (self, cr, uid, context=None):
#         return self.pool.get('base.element').get_as_selection(cr, uid, 'PE.SUNAT.TABLA_01', context=context)
#
#     _columns = {
#         'sunat_payment_code': fields.selection(_get_payment_code_selection, "Medio de Pago",
#                                                help="Medio de pago, de acuerdo a SUNAT Tabla 01"),
#     }
    
class res_partner_bank(osv.Model):
    _inherit = "res.bank"

    def _get_bank_code_selection (self, cr, uid, context=None):
        bt_obj = self.pool.get('base.element')
    
        return bt_obj.get_as_selection(cr, uid, 'PE.SUNAT.TABLA_03', context=context)
    
    _columns = {
        'sunat_bank_code': fields.selection(_get_bank_code_selection, "Bank code", 
                                            help="Entidad financiera, according to SUNAT Table 03"),    
    }

class res_currency(osv.Model):
    _inherit = "res.currency"

    def _get_sunat_code_selection (self, cr, uid, context=None):
        bt_obj = self.pool.get('base.element')
    
        return bt_obj.get_as_selection(cr, uid, 'PE.SUNAT.TABLA_04', context=context)
    
    _columns = {
        'sunat_code': fields.selection(_get_sunat_code_selection, "SUNAT code", 
                                       help="Tipo de moneda, according to SUNAT Table 04"),    
    }

class product_category(osv.Model):
    _inherit = "product.category"

    def _get_sunat_code_selection (self, cr, uid, context=None):
        bt_obj = self.pool.get('base.element')
    
        return bt_obj.get_as_selection(cr, uid, 'PE.SUNAT.TABLA_05', context=context)
    
    def _get_sunat_catalogo_selection (self, cr, uid, context=None):
        bt_obj = self.pool.get('base.element')
    
        return bt_obj.get_as_selection(cr, uid, 'PE.SUNAT.TABLA_13', context=context)

    def _get_sunat_inventory_type(self, cr, uid, ids, fields, args, context=None):
        res = {}
        for pc in self.read(cr, uid, ids, ['sunat_code', 'parent_id'], context=context):
            if pc['sunat_code']:
                res[pc['id']] = pc['sunat_code']
            elif pc['parent_id']:
                parent = self.browse(cr, uid, pc['parent_id'] [0], context=context)
                res[pc['id']] = parent.sunat_code
            else:
                res[pc['id']] = False
        return res
        
    def _get_sunat_inventory_display_type(self, cr, uid, ids, fields, args, context=None):
        res = {}
        vals = self._get_sunat_inventory_type(cr, uid, ids, fields, args, context=context)
        selection = {}
        for x in self._get_sunat_code_selection(cr, uid, context=context): selection[x[0]]=x[1] 
        for k in vals.keys():
            if vals[k]:
                res[k] = selection[vals[k]]
            else:
                res[k] = ''
        return res
        
    _columns = {
        'sunat_tipo_existencia': fields.selection(_get_sunat_catalogo_selection, "SUNAT Inventory Catalog",
                                                  help="Código del catálogo utilizado. Sólo se podrá incluir las opciones 3 y 9 de la tabla 13."),
        'sunat_code': fields.selection(_get_sunat_code_selection, "SUNAT inventory type code", 
                                       help="Tipo de existencia, according to SUNAT Table 05"),
        'osce_code': fields.many2one('base.element', "OSCE-CUBSO-UNSPSC code", domain=[('table_id.code','=','UN.UNSPSC')], 
                                       help="Código de la existencia, de acuerdo al Catálogo de Bienes, Servicios y Obras (*)  establecido por el Organismo Supervisor de las Contrataciones del Estado (OSCE) y vigente al 01 de enero de cada año., according to UNSPSC and CUBSO Tables"),    
        'sunat_inventory_type': fields.function(_get_sunat_inventory_type, string="Inventory type", type="char", 
                                                 help="SUNAT code, for this category or the first in parent's chain"),
        'sunat_inventory_display_type': fields.function(_get_sunat_inventory_display_type, string="Inventory type", type="char", 
                                                 help="SUNAT code, for this category or the first in parent's chain"),
    }

class product_uom(osv.Model):
    _inherit = "product.uom"
        
    def _get_sunat_code_selection (self, cr, uid, context=None):
        bt_obj = self.pool.get('base.element')
    
        return bt_obj.get_as_selection(cr, uid, 'PE.SUNAT.TABLA_06', context=context)

    _columns = {
        'sunat_code': fields.many2one('base.element', "SUNAT code", domain=[('table_id.code','=','PE.SUNAT.TABLA_06')], 
                                       help="Tipo de existencia, according to SUNAT Table 06"),
    }

class product_template(osv.Model):
    _inherit = "product.template"

    def _get_sunat_valuation_method_selection (self, cr, uid, context=None):
        bt_obj = self.pool.get('base.element')
    
        return bt_obj.get_as_selection(cr, uid, 'PE.SUNAT.TABLA_14', context=context)

    def _get_sunat_title_type_selection (self, cr, uid, context=None):
        bt_obj = self.pool.get('base.element')
    
        return bt_obj.get_as_selection(cr, uid, 'PE.SUNAT.TABLA_15', context=context)

    def _get_sunat_share_type_selection (self, cr, uid, context=None):
        bt_obj = self.pool.get('base.element')
    
        return bt_obj.get_as_selection(cr, uid, 'PE.SUNAT.TABLA_16', context=context)

    def _get_sunat_asset_type_selection (self, cr, uid, context=None):
        bt_obj = self.pool.get('base.element')
    
        return bt_obj.get_as_selection(cr, uid, 'PE.SUNAT.TABLA_18', context=context)

    def _get_sunat_asset_state_selection (self, cr, uid, context=None):
        bt_obj = self.pool.get('base.element')
    
        return bt_obj.get_as_selection(cr, uid, 'PE.SUNAT.TABLA_19', context=context)

    def _get_sunat_asset_depreciation_method_selection (self, cr, uid, context=None):
        bt_obj = self.pool.get('base.element')
    
        return bt_obj.get_as_selection(cr, uid, 'PE.SUNAT.TABLA_20', context=context)

    _columns = {
        'sunat_title_type': fields.selection(_get_sunat_title_type_selection, "SUNAT title type", 
                                             help="Tipo de título, according to SUNAT Table 15"),    
        'sunat_share_type': fields.selection(_get_sunat_share_type_selection, "SUNAT share type", 
                                             help="Tipo de acciones o participaciones, according to SUNAT Table 16"),    
        'sunat_valuation_method': fields.selection(_get_sunat_valuation_method_selection, "SUNAT valuation method", 
                                                   help="Método de valuación, according to SUNAT Table 14"),
        'sunat_asset_type': fields.selection(_get_sunat_asset_type_selection, "SUNAT asset type", 
                                             help="Tipo de activo fijo, according to SUNAT Table 18"),    
        'sunat_asset_state': fields.selection(_get_sunat_asset_state_selection, "SUNAT asset state", 
                                             help="Estado del activo fijo, according to SUNAT Table 19"),    
        'sunat_depreciation_method': fields.selection(_get_sunat_asset_depreciation_method_selection, "SUNAT depreciation method", 
                                             help="Método de depreciación, according to SUNAT Table 20"),
    }

class product_product(osv.Model):
    _inherit = "product.product"

    _columns = {
        'sunat_nominal_value': fields.float('Title/share nominal value x unit', digits=(14,2)),
        'sunat_acum_depreciation': fields.float('Acumulated depreciaton x unit', digits=(14,2)),
    }

class stock_picking(osv.Model):
    _name = "stock.picking"
    _inherit = "stock.picking"

    _columns = {
        'remision_number': fields.char('Remision Number', 32, states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),   
    }

class stock_move(osv.Model):
    _inherit = "stock.move"

    _columns = {
        'remision_number': fields.related('picking_id','remision_number',string='Remision Number', type='char', readonly=True),
    }

class stock_location(osv.Model):
    _inherit = "stock.location"
    
    def _get_sunat_op_type_selection (self, cr, uid, context=None):
        return self.pool.get('base.element').get_as_selection(cr, uid, 'PE.SUNAT.TABLA_12', context=context)
    
    _columns = {
        'sunat_branch_code': fields.char('Branch Code', 7, help="""Código de establecimiento anexo:
1. Los cuatro primeros dígitos son obligatorios y corresponden al código de establecimiento anexo según el Registro Único de Contribuyentes. 
2. En caso el almacén se encuentre ubicado en el establecimiento de un tercero o no sea posible incluirlo como un establecimiento anexo, los cuatro primeros números serán: "9999" 
3. De la posición 5 a la 7 registrar un correlativo, de ser necesario"""),
        'sunat_op_type_in': fields.selection(_get_sunat_op_type_selection, "SUNAT operation type IN", 
                                             help="Tipo de operación de entrada, according to SUNAT Table 12"),
        'sunat_op_type_out': fields.selection(_get_sunat_op_type_selection, "SUNAT operation type OUT", 
                                             help="Tipo de operación de salida, according to SUNAT Table 12"),
    }
    
class res_company(osv.Model):
    _inherit = "res.company"

    def _get_sunat_accounting_plan_selection (self, cr, uid, context=None):
        bt_obj = self.pool.get('base.element')
        return bt_obj.get_as_selection(cr, uid, 'PE.SUNAT.TABLA_17', context=context)

    def _get_financial_catalog_selection(self, cr, uid, context=None):
        bt_obj = self.pool.get('base.element')
        return bt_obj.get_as_selection(cr, uid, 'PE.SUNAT.TABLA_22', context=context)

    _columns = {
        'sunat_accounting_plan': fields.selection(_get_sunat_accounting_plan_selection, "SUNAT accounting plan", 
                                             help="Plan de cuentas, according to SUNAT Table 17"),
        'sunat_financial_catalog': fields.selection(_get_financial_catalog_selection, "Financial catalog",
                                                    help="Catálogo de estados financieros, according to SUNAT Table 22"),
    }

class account_asset_category(osv.Model):
    _inherit = "account.asset.category"

    def _get_sunat_code_selection (self, cr, uid, context=None):
        bt_obj = self.pool.get('base.element')
        return bt_obj.get_as_selection(cr, uid, 'PE.SUNAT.TABLA_13', context=context)

    _columns = {
        'sunat_code': fields.selection(_get_sunat_code_selection, "SUNAT code", 
                                       help="Catálogo de existencias, according to SUNAT Table 13"),    
    }

class account_asset_asset(osv.Model):
    _inherit = "account.asset.asset"

    def _get_sunat_asset_type_selection (self, cr, uid, context=None):
        bt_obj = self.pool.get('base.element')
    
        return bt_obj.get_as_selection(cr, uid, 'PE.SUNAT.TABLA_18', context=context)

    def _get_sunat_asset_state_selection (self, cr, uid, context=None):
        bt_obj = self.pool.get('base.element')
    
        return bt_obj.get_as_selection(cr, uid, 'PE.SUNAT.TABLA_19', context=context)

    def _get_sunat_asset_depreciation_method_selection (self, cr, uid, context=None):
        bt_obj = self.pool.get('base.element')
    
        return bt_obj.get_as_selection(cr, uid, 'PE.SUNAT.TABLA_20', context=context)

    _columns = {
        'sunat_asset_type': fields.selection(_get_sunat_asset_type_selection, "SUNAT asset type", 
                                             help="Tipo de activo fijo, according to SUNAT Table 18"),    
        'sunat_asset_state': fields.selection(_get_sunat_asset_state_selection, "SUNAT asset state", 
                                             help="Estado del activo fijo, according to SUNAT Table 19"),    
        'sunat_depreciation_method': fields.selection(_get_sunat_asset_depreciation_method_selection, "SUNAT depreciation method", 
                                             help="Método de depreciación, according to SUNAT Table 20"),    
    }

class account_analytic_account(osv.Model):
    _inherit = "account.analytic.account"

    def _get_sunat_production_grouping_selection (self, cr, uid, context=None):
        bt_obj = self.pool.get('base.element')
    
        return bt_obj.get_as_selection(cr, uid, 'PE.SUNAT.TABLA_21', context=context)

    _columns = {
        'sunat_production_grouping': fields.selection(_get_sunat_production_grouping_selection, "SUNAT production grouping", 
                                             help="Código de agrupamiento del costo de producción valorizado anual, according to SUNAT Table 21"),    
    }

class res_partner(osv.osv):
    _inherit = 'res.partner'
    
    def _get_doc_types(self, cr, uid, context=None):
        return self.pool.get('base.element').get_as_selection(cr, uid, 'PE.SUNAT.TABLA_02', context=context)
    
    def _get_bienes_servicios(self, cr, uid, context=None):
        return self.pool.get('base.element').get_as_selection(cr, uid, 'PE.SUNAT.TABLA_30', context=context)
    
    def _get_vinculacion(self, cr, uid, context=None):
        return self.pool.get('base.element').get_as_selection(cr, uid, 'PE.SUNAT.TABLA_27', context=context)
    
    _columns = {
        'doc_type': fields.selection (_get_doc_types, 'Document type'),
        'doc_number': fields.char('Document Number',32,select=1),
        'sunat_bienes_servicios': fields.selection (_get_bienes_servicios, 'Bienes / Servicios', help="""Clasificación de los bienes y servicios adquiridos (Tabla 30)
Aplicable solo a los contribuyentes que hayan obtenido ingresos mayores a 1,500 UIT en el ejercicio anterior"""),
        'sunat_renuncia_exon_igv': fields.boolean('Renuncia Exoneración IGV', help="RUCs que renunciaron a la exoneración del IGV"),
        'sunat_renuncia_exon_date': fields.date('Fecha Renuncia', help="Fecha de la Renuncia a la Exoneración del IGV"),
        'sunat_vinculacion': fields.selection (_get_doc_types, 'Vinculación', help="Vínculo entre el contribuyente y el residente en el extranjero"),
    }
    #_sql_constraints = [('doc_number_unique','unique(doc_number)','The document number must be unique!'),]
    
    def vat_change(self, cr, uid, ids, value, context=None):
        res = super (res_partner, self).vat_change(cr, uid, ids, value, context=context)
        if not res:
            res = {'value':{}}
            
        if value and len(value)>2:
            if value[:2] == 'PE' and len(value[2:])==11:
                res['value']['doc_type'] = '6'
            elif value[:2] == 'CC' and len(value[2:])==8:
                res['value']['doc_type'] = '1'
            else:
                res['value']['doc_type'] = '0'
            res['value']['doc_number'] = value[2:]
        return res

    def onchange_is_company (self, cr, uid, ids, is_company, doc_type, context=None):
        res = super (res_partner, self).onchange_type(cr, uid, ids, is_company, context=context)
        res['value']['doc_type'] = is_company and '6' or '1'
#        if is_company and doc_type != '6':
#            raise osv.except_osv (_('Value error'),
#                   _('Companies should be identified by RUC only! Please check!'))
        return res
        
    def onchange_doc (self, cr, uid, ids, doc_type, doc_number, is_company, context=None):
        res = {'value':{},'warning':{}}

        if doc_number and is_company and (doc_type != '6'):
            res['warning']['title'] = _('Value error')
            res['warning']['message'] = _('Companies should be identified by RUC only! Please check!')
            
        if doc_number and doc_type == '0':
            if (not doc_number) or len (doc_number) > 15:
                res['warning']['title'] = _('Value error')
                res['warning']['message'] = _('Document number should be alfanumeric, not longer than 15 characters! Please check!')
        elif doc_number and doc_type == '1':
            if (not doc_number) or len (doc_number) != 8 or not doc_number.isdigit():
                res['warning']['title'] = _('Value error')
                res['warning']['message'] = _('Libreta electoral or DNI should be numeric, exactly 8 numbers long! Please check!')
            details=self.get_partner_details(cr, uid, doc_number, context=context)
            if details.has_key('warning'):
                res['warning'] = details['warning']
            else:
                res['value'].update(details)
            res['value']['vat'] = doc_number and 'CC' + doc_number 
        elif doc_number and doc_type == '4':
            if (not doc_number) or len (doc_number) > 12:
                res['warning']['title'] = _('Value error')
                res['warning']['message'] = _('Carnet de extranjeria should be alfanumeric, not longer than 12 characters! Please check!')
        elif doc_number and doc_type == '6':
            if (not doc_number) or (len (doc_number) < 8 or len (doc_number) > 11) or not doc_number.isdigit():
                res['warning']['title'] = _('Value error')
                res['warning']['message'] = _('RUC should be numeric, 8-11 numbers long! Please check!')
            res['value']['vat'] = doc_number and 'PE' + doc_number
            details=self.get_company_details(cr, uid, doc_number, context=context)
            if details.has_key('warning'):
                res['warning'] = details['warning']
            else:
                res['value'].update(details)
        elif doc_number and doc_type == '7':
            if (not doc_number) or len (doc_number) > 12:
                res['warning']['title'] = _('Value error')
                res['warning']['message'] = _('Pasaporte should be alfanumeric, not longer than 12 characters! Please check!')
        elif doc_number and doc_type == 'A':
            if (not doc_number) or len (doc_number) != 15 or not doc_number.isdigit():
                res['warning']['title'] = _('Value error')
                res['warning']['message'] = _('Cedula diplomatica should be numeric, exactly 15 numbers long! Please check!')

        return res
        
class res_country(osv.osv):
    _inherit = 'res.country'
    
    def _get_country(self, cr, uid, context=None):
        return self.pool.get('base.element').get_as_selection(cr, uid, 'PE.SUNAT.TABLA_35', context=context)
    
    def _get_agreement(self, cr, uid, context=None):
        return self.pool.get('base.element').get_as_selection(cr, uid, 'PE.SUNAT.TABLA_25', context=context)
    
    _columns = {
        'sunat_code': fields.selection (_get_country, 'SUNAT Code'),
        'sunat_agreement': fields.selection (_get_agreement, 'SUNAT Agreement', help="Convenios para evitar la doble imposición"),
    }


class account_account_type(osv.osv):
    _inherit = 'account.account.type'

    _columns = {
        'sunat_code': fields.many2one('base.element', "SUNAT code", domain=[('table_id.code','=','PE.SUNAT.TABLA_34')],
                                       help="SUNAT financial report type, according to SUNAT Table 34"),
    }
