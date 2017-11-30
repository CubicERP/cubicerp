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

from openerp.osv import fields, osv
from openerp.tools.translate import _
import base64
import time

class sunat_file_save (osv.TransientModel):
    _name = 'l10n_pe.sunat_file_save'
    
    _columns = {
        'output_name': fields.char ('Output filename', size=128),
        'output_file': fields.binary ('Output file', readonly=True, filename="output_name"),    
    }

class ple (osv.AbstractModel):
    _name = "l10n_pe.ple"
    _inherit = ['mail.thread','ir.needaction_mixin']

    def _get_oportunity_selection(self, cr, uid, context=None):
        return self.pool.get('base.element').get_as_selection(cr, uid, 'PE.SUNAT.REGLA_NOMBRE_CC', context=context)

    def _get_operation_selection(self, cr, uid, context=None):
        return self.pool.get('base.element').get_as_selection(cr, uid, 'PE.SUNAT.REGLA_NOMBRE_O', context=context)
    
    _columns = {
        'company_id': fields.many2one ('res.company', 'Company', required=True, readonly=True, states={'draft':[('readonly',False)],}),
        'period_id': fields.many2one ('account.period', 'Period', required=True, domain="[('company_id','=',company_id)]", readonly=True, states={'draft':[('readonly',False)],}),
        'journal_id': fields.many2one ('account.journal', 'Journal', domain="[('company_id','=',company_id)]", readonly=True, states={'draft':[('readonly',False)],}),
        'oportunity_code': fields.selection(_get_oportunity_selection, string="Oportunity Code", required=True),
        'operation_code': fields.selection(_get_operation_selection, string="Operation Code", required=True),
        'state' : fields.selection ([
                        ('draft', 'Draft'),
                        ('loaded', 'Loaded'),
                        ('numbered', 'Numbered'),
                        ('issued', 'Issued'),
                        ], 'State', readonly=True),
    }    

    _defaults = {
        'state': 'draft',
        'oportunity_code': '07',
        'operation_code': '1',
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'l10n_pe.ple', context=c),
    }

    #_sql_constraints = [('report_name_unique','unique(company_id,period_id)',_('Only one report per company and period is allowed!'))]
    
    def unlink(self, cr, uid, ids, context=None):
        for p in self.browse(cr, uid, ids, context=context):
            if not p.state == 'draft':
                raise osv.except_osv (_('Unlink Error'),
                                      _('The report must be on draft state to delete it'))
        return super(ple,self).unlink(cr, uid, ids, context=context)
    
    def onchange_state (self, cr, uid, ids, state, context=None):
        if ids and state:
            ple = self.browse (cr, uid, ids[0], context=context)
            if ple.state == 'issued':
                raise osv.except_osv (_('Action error'),
                       _('You can not get back to "draft" an issued report!'))
        return False

    def get_all_periods_up_to (self, cr, uid, period_id, context=None):
        period_obj = self.pool.get('account.period')
        period = period_obj.browse(cr, uid, period_id, context=context)
        period_ids = period_obj.search (cr, uid, 
                                        [('fiscalyear_id', '=', period.fiscalyear_id.id), ('date_start','<=',period.date_start)], 
                                        context=context)
        return period_ids
        
    def get_move_lines (self, cr, uid, period_id, report_type, 
                          company_id=None, account_ids=None, journal_ids=None, partner_ids=None, product_ids=None, context=None):
        if context is None:
            context = {}
        conf_obj = self.pool.get('l10n_pe.ple_configuration')
        move_line_obj = self.pool.get('account.move.line')
        period_obj = self.pool.get('account.period')

        if isinstance(period_id, (int, long)):
            period_ids = [period_id]
        else:
            period_ids = period_id

        if not company_id:
            periods = period_obj.browse(cr, uid, period_ids, context=context)
            company_id = periods[0].company_id.id

        conf_ids = conf_obj.search(cr, uid, [('company_id', '=', company_id), ('report_type','=',report_type)], context=context)
        if conf_ids and len(conf_ids)==1:
            conf = conf_obj.browse(cr, uid, conf_ids[0], context=context)
            search_expr = [('move_id.state','=','posted')]

            search_expr += [('period_id','in', period_ids)]

            if partner_ids:
                search_expr += [('partner_id',context.get('ple_config_patner_operator','in'), partner_ids)]

            if product_ids:
                search_expr += [('product_id',context.get('ple_config_product_operator','in'), product_ids)]

            if journal_ids:
                search_expr += [('journal_id',context.get('ple_config_journal_operator','in'), journal_ids)]
            elif conf.journals_ids:
                search_expr += [('journal_id',context.get('ple_config_journal_operator','in'), [j.id for j in conf.journals_ids])]

            if account_ids:
                search_expr += [('account_id',context.get('ple_config_account_operator','in'), account_ids)]
            elif conf.accounts_ids:
                search_expr += [('account_id',context.get('ple_config_account_operator','in'),[j.id for j in conf.accounts_ids or []])]

            move_line_ids = move_line_obj.search(cr, uid, search_expr, context=context)
            if move_line_ids:
                return move_line_obj.browse(cr, uid, move_line_ids, context=context)
            else:
                return []
        else:
            company = self.pool.get('res.company').browse(cr, uid, company_id, context=context)
            raise osv.except_osv (_('Configuration error'),
                   _('No data for report SUNAT %(report_type)s for company [%(company)s]!') % {
                           'report_type': report_type,
                           'company': company.name})

    def action_confirm (self, cr, uid, ids, context=None):
        assert ids and len(ids)==1
        ple = self.browse (cr, uid, ids[0], context=context)
        return ple.write ({'state': 'issued'}, context=context)
    
    def action_draft (self, cr, uid, ids, context=None):
        assert ids and len(ids)==1
        ple = self.browse (cr, uid, ids[0], context=context)
        return ple.write ({'state': 'draft'}, context=context)
        
    def action_reload (self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state':'loaded'}, context=context)

    def action_renumber (self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state':'numbered'}, context=context)

    def action_report (self, cr, uid, ids, context=None):
        # To be defined by subclasses
        raise osv.except_osv (_('Action error'),
               _('Subclass has not implemented report action!'))
    
    def action_save_file (self, cr, uid, ids, context=None):
        sfs_obj = self.pool.get('l10n_pe.sunat_file_save')

        encoded_lines = [l.encode('utf-8') for l in self.get_output_lines(cr, uid, ids, context=context)]
        encoded_output_file = base64.b64encode('\n'.join(encoded_lines))
        file_name = self.get_output_filename(cr, uid, ids, context=context)

        vals = {
            'output_name': encoded_output_file and file_name or "%s0%s"%(file_name[:-7],file_name[-6:]),
            'output_file': encoded_output_file or '===',
        }
        
        sfs_id = sfs_obj.create (cr, uid, vals, context=context)
        
        self.action_confirm(cr, uid, ids, context=context)
        
        return {
            'name':_("Save output file"),
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'l10n_pe.sunat_file_save',
            'res_id': sfs_id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': "",
            'context': dict(context)
        }
    
    def convert_date (self, s):
        if s:
            return time.strftime('%d/%m/%Y', time.strptime(s,'%Y-%m-%d'))
        else:
            return "01/01/0001"
    
    def convert_str (self, s):
        return s and unicode(s).replace('|','-').replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u').replace('Á','A').replace('É','E').replace('Í','I').replace('Ó','O').replace('Ú','U').replace('\n',' ').replace('/','') or ''
        
    def convert_amount (self, a):
        return a and unicode(a) or '0.00'
        
    def convert_qty (self, q):
        return q and unicode(q) or '0'
    
    def convert_document_serie(self, document, serie, context=None):
        if serie and len(serie)<4 and document in ('56','48','36','35','34','25','23','08','07','06','04','03','01'):
            serie = serie.zfill(4)
        return self.convert_str(serie)
    
    def get_output_lines (self, cr, uid, ids, context=None):
        # To be defined by subclasses
        # It should return a list of strings, each of them representing an output line
        assert ids and len(ids)==1
        ple = self.browse (cr, uid, ids[0], context=context)

        res = []
        if not ple.company_id.partner_id.vat:
            raise osv.except_osv (_('Value error'),
                _('The VAT number of the company is a mandatory field. It could not be blank! Please check it on company form'))
        return res

    def get_output_filename (self, cr, uid, ids, context=None):
        # To be defined by subclasses
        # It should return the name of the output file
        
        raise osv.except_osv (_('Action error'),
               _('Subclass has not implemented output filename action!'))
        

class ple_line(osv.AbstractModel):
    _name = 'l10n_pe.ple_line'
    
    _columns = {
        'sequence': fields.integer ('Sequence'),
        'period_id': fields.many2one ('account.period', 'Period', required=True, select=1),
        'move_line_id': fields.many2one('account.move.line', 'Accounting movement', select=1),
        'account_id': fields.many2one('account.account', 'Account', domain="[('company_id','=',company_id)])"),
    }
    
    def _get_cuo_sequence(self, move_line, context=None):
        if context is None:
            context = {}
        cuo = "%s"%(move_line.move_id.name)
        oi = cuo.split('-')
        if len(oi) == 1:
            oi = cuo.split('/')
        os = move_line.period_id.date_start[5:7] == '12' and 'C' or "A" if move_line.period_id.special else "M"
        return cuo, "%s%s" % (os,oi[-1])

    def _get_document_serie_number(self, move_line, invoice=False, context=None):
        invoice = invoice or move_line.invoice
        if invoice.journal_id:
            document = invoice.journal_id.sunat_payment_type or '00'
            journal = invoice.journal_id
        else:
            document = move_line.journal_id.sunat_payment_type or '00'
            journal = move_line.journal_id
        if journal.type in ['sale', 'sale_refund']:
            s = invoice and invoice.internal_number and invoice.internal_number.split('-') or move_line.move_id.name.split('-')
            serie = len(s)>1 and s[-2] or ''
            number = s[-1]
        else:
            if move_line.journal_id.sunat_payment_type and document in ('50','51','52','53','54'):
                serie = move_line.journal_id.sunat_customs_code
                s = invoice and invoice.supplier_invoice_number and invoice.supplier_invoice_number.split('-') or move_line.move_id.name.split('-')
                number = len(s)>1 and s[-2] or s[-1]
            else:
                s = invoice and invoice.supplier_invoice_number and move_line.invoice.supplier_invoice_number.split('-') or move_line.move_id.name.split('-')
                serie = move_line.journal_id.sunat_payment_type and len(s)>1 and s[-2] or ''
                number = move_line.journal_id.sunat_payment_type and s[-1] or '0'
        return document, serie, number

class ple_configuration (osv.Model):
    _name = "l10n_pe.ple_configuration"
    
    def _get_report_type (self, cr, uid, context=None):
        return self.get_report_type(cr, uid, context=context)

    _columns = {
        'company_id': fields.many2one ('res.company', 'Company', required=True, on_delete='cascade'),
        'report_type': fields.selection (_get_report_type, 'Report type', required=True),
        'accounts_ids': fields.many2many ('account.account', 'l10n_pe_conf_account', 'conf_id', 'account_id', 'Target accounts', domain="[('company_id','=',company_id)]"),
        'journals_ids': fields.many2many ('account.journal', 'l10n_pe_conf_journal', 'conf_id', 'journal_id', 'Target journals', domain="[('company_id','=',company_id)]"),
    }    
    
    _defaults = {
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'l10n_pe.ple', context=c),
    }

    def get_report_type (self, cr, uid, context=None):
        # To be subclassed
        # Returns a list of tuples for the report type selection field
        
        return []

