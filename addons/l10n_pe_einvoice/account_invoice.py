## -*- encoding: utf-8 -*-
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

from openerp import models, fields, api, _
from openerp.exceptions import Warning, except_orm
import openerp.addons.decimal_precision as dp
from datetime import date
#from pdf417gen import encode, render_image
import base64
import tempfile
from openerp.tools.float_utils import float_round as round
try:
    import qrcode
    qr_mod = True
except:
    qr_mod = False
from openerp import report


class account_invoice(models.Model):
    _name = "account.invoice"
    _inherit = "account.invoice"
    
    @api.model
    def _get_pe_qrcode(self):
        res=[]
        for invoice_id in self:
            if invoice_id.type=="out_invoice" and invoice_id.internal_number and qr_mod:
                res.append(invoice_id.company_id.vat and invoice_id.company_id.vat[2:] or '')
                res.append(invoice_id.journal_id.sunat_payment_type or '')
                res.append(invoice_id.internal_number or '')
                precision = self.env['decimal.precision'].precision_get('Account')
                res.append(str(round(invoice_id.amount_tax*(invoice_id.discount and (1-invoice_id.discount/100) or 1), precision)) or '')
                res.append(str(invoice_id.amount_total))
                res.append(invoice_id.date_invoice)
                if invoice_id.partner_id.doc_type and invoice_id.partner_id.doc_number:
                    res.append(invoice_id.partner_id.doc_type)
                    res.append(invoice_id.partner_id.doc_number)
                qr_string='|'.join(res)
                qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_Q)
                qr.add_data(qr_string)
                qr.make(fit=True)
                qr_pic = qr.make_image()
                f = tempfile.TemporaryFile(mode="r+")
                qr_pic.save(f,'png')
                f.seek(0)
                invoice_id.sunat_qr_code = base64.encodestring(f.read())
    
#     @api.model
#     def _get_pe_bar_code(self):
#         res=[]
#         if self.type=="out_invoice" and self.internal_number and self.batch_pe_id:
#             res.append(self.company_id.vat and self.company_id.vat[2:] or '')
#             res.append(self.journal_id.sunat_payment_type or '')
#             res.append(self.internal_number or '')
#             precision = self.env['decimal.precision'].precision_get('Account')
#             res.append(str(round(self.amount_tax*(self.discount and (1-self.discount/100) or 1), precision)) or '')
#             res.append(str(self.amount_total))
#             res.append(self.date_invoice or '')
#             if self.partner_id.doc_type and self.partner_id.doc_number:
#                 res.append(self.partner_id.doc_type)
#                 res.append(self.partner_id.doc_number)
#             res.append(self.batch_pe_id.signature or '')
#             res.append(self.batch_pe_id.digest or '')
#             bar_string='|'.join(res)
#             codes = encode(bar_string, columns=12, security_level=5)
#             image = render_image(codes)               
#             f = tempfile.TemporaryFile(mode="r+")
#             image.save(f,'png')
#             f.seek(0)
#             self.sunat_bar_code = base64.encodestring(f.read())
    
    @api.model
    def _get_sunat_invoice_name(self):
        for invoice in self:
            if invoice.journal_id and invoice.journal_id.sunat_payment_type:
                res=self.env['base.element'].search([('name','=',invoice.journal_id.sunat_payment_type),('table_id.code','=', 'PE.SUNAT.TABLA_10')])
                invoice.sunat_invoice_name="%s %s" % (res.description, _("Electronic"))
            elif invoice.type == 'out_invoice' and (invoice.state == 'open' or invoice.state == 'paid'):
                invoice.sunat_invoice_name=_('Invoice')
            elif invoice.type == 'out_invoice' and invoice.state == 'proforma2':
                invoice.sunat_invoice_name=_('PRO-FORMA')
            elif invoice.type == 'out_invoice' and invoice.state == 'draft':
                invoice.sunat_invoice_name=_('Draft Invoice')
            elif invoice.type == 'out_invoice' and invoice.state == 'cancel':
                invoice.sunat_invoice_name=_('Cancelled Invoice')
            elif invoice.type == 'out_refund':
                invoice.sunat_invoice_name=_('Refund')
            elif invoice.type == 'in_refund':
                invoice.sunat_invoice_name=_('Supplier Refund')
            elif invoice.type == 'in_invoice':
                invoice.sunat_invoice_name=_('Supplier Invoice')
            else:
                invoice.sunat_invoice_name=_('Invoice')
        
    @api.one
    @api.depends('batch_pe_id','batch_pe_id.status_code','batch_pe_id.emessage_ids.status_code')
    def _status_code(self):
        if self.batch_pe_id:
            for message in self.batch_pe_id.emessage_ids:
                if message.status_code:
                    self.status_code = message.status_code
                    break
        
    @api.model
    def _get_status_code(self):
        return self.env['base.element'].get_as_selection('PE.SEE.ERROR')
    
    @api.model
    def _get_credit_note(self):
        return self.env['base.element'].get_as_selection('PE.SEE.CATALOGO_09')
    
    @api.model
    def _get_debit_note(self):
        return self.env['base.element'].get_as_selection('PE.SEE.CATALOGO_10')
    
    @api.one
    @api.depends('invoice_line.price_subtotal', 'tax_line.amount')
    def _compute_amount_sunat(self):
        disc = 0.0
        gift = 0.0
        total= 0.0
        exonerated = 0.0
        for inv in self:
            for line in inv.invoice_line:
                taxes = line.invoice_line_tax_id.compute_all(line.price_unit, 1, product=line.product_id, partner=line.invoice_id.partner_id)
                disc += line.invoice_id.currency_id.round((taxes['total']* line.discount / 100) * line.quantity)
                if line.discount==100:
                    gift += line.price_unit * line.quantity
                if line.price_subtotal<0:
                    total += line.price_subtotal
                if not line.invoice_line_tax_id and line.price_subtotal>0:
                    exonerated+=line.price_subtotal
        self.amount_gift=self.currency_id.round(gift)
        self.amount_discount=self.currency_id.round(disc)
        self.amount_disc_total=self.currency_id.round(-total)
        self.amount_exonerated=self.currency_id.round(exonerated)
    
    @api.one
    @api.depends('invoice_line.price_subtotal', 'tax_line.amount', 'amount_untaxed', 'amount_disc_total')
    def _compute_discount_sunat(self):
        disc = 0.0
        for inv in self:
            for line in inv.invoice_line:
                if line.price_subtotal<0:
                    disc += line.price_subtotal
        self.discount=-(self.amount_untaxed and disc*100/(self.amount_untaxed+self.amount_disc_total)) or 0         
    
    status_code = fields.Selection(_get_status_code, string='Status Code', readonly=True, compute=_status_code, store=True)
    batch_pe_id = fields.Many2one('einvoice.batch.pe', string='Electronic Batch Perú', readonly=True, 
                                        domain=[('state','=','draft')], copy=False,
                                        states={'draft':[('readonly',False)],})
    batch_voided_pe_id = fields.Many2one('einvoice.batch.pe', string='Electronic Batch Perú', readonly=True, 
                                        domain=[('state','=','draft')],
                                        states={'draft':[('readonly',False)],})
    batch_summary_pe_id = fields.Many2one('einvoice.batch.pe', string='Electronic Batch Perú', readonly=True, 
                                        domain=[('state','=','draft')],
                                        states={'draft':[('readonly',False)],})
    sunat_add_line=fields.One2many('account.invoice.sunat.add', 'invoice_id', string="Sunat additional",
                                   readonly=True, states={'draft': [('readonly', False)]}, copy=False)
    credit_note_type = fields.Selection(_get_credit_note, string='Credit note type', store=True, default='01')
    debit_note_type = fields.Selection(_get_debit_note, string='Debit note type', store=True)
    sunat_payment_type=fields.Selection(string='Debit note type', related='journal_id.sunat_payment_type', readonly=True)
    amount_discount = fields.Float(string='Amount Discount',
                                   digits=dp.get_precision('Account'),
                                   readonly=True, compute='_compute_amount_sunat')
    amount_disc_total = fields.Float(string='Discount from total',
                                   digits=dp.get_precision('Account'),
                                   readonly=True, compute='_compute_amount_sunat')
    amount_gift = fields.Float(string='Total gift', digits=dp.get_precision('Account'),
                                readonly=True, compute='_compute_amount_sunat')
    amount_exonerated = fields.Float(string='Total exonerated', digits=dp.get_precision('Account'),
                                readonly=True, compute='_compute_amount_sunat')
    discount = fields.Float(string='Discount percentage', digits=dp.get_precision('Discount'),
                                readonly=True, compute='_compute_discount_sunat')
    batch_pe_type=fields.Selection(string='Batch type', related='batch_voided_pe_id.type', readonly=True)
    sunat_qr_code=fields.Binary("QR code", compute=_get_pe_qrcode)
#    sunat_bar_code=fields.Binary("Bar code", compute=_get_pe_bar_code)
    sunat_invoice_name=fields.Char("Sunat Invoice Name", compute=_get_sunat_invoice_name)
    
    @api.one
    def validate_pe_invoice(self):
        if self.partner_id.doc_number and self.journal_id.sunat_payment_type in ['01','03', '07', '08']:
            if self.journal_id.sunat_payment_type=='03' and self.partner_id.doc_type == '6':
                raise except_orm('SUNAT Error','El tipo de documento del adquiriente no puede ser Numero de RUC')
            if self.journal_id.sunat_payment_type=='01' and self.partner_id.doc_type == '1':
                raise except_orm('SUNAT Error','El tipo de documento del adquiriente no puede ser Numero de DNI')
            
        elif not self.partner_id.doc_number and self.journal_id.sunat_payment_type=='03' and self.amount_total>=700:
            raise except_orm('SUNAT Error','Si el monto total es mayor a S/. 700.00 debe consignar tipo y numero de documento del adquiriente')
            
     
    @api.multi
    def invoice_validate(self):
        for invoice in self:
            if invoice.journal_id.is_einvoice_pe:
                invoice.validate_pe_invoice()
        res= super(account_invoice,self).invoice_validate()
        
        for invoice in self:
            if invoice.journal_id.is_einvoice_pe:
                element_15_02=True
                for line in invoice.sunat_add_line:
                    if line.element_id.id==self.env.ref('l10n_pe_einvoice.element_15_01').id:
                        line.unlink()
                        continue
                    if line.element_id.id==self.env.ref('l10n_pe_einvoice.element_15_02').id:
                        element_15_02=False
                if element_15_02:
                    for line in invoice.invoice_line:
                        if line.discount==100:
                            self.sunat_add_line.create({'name':self.env.ref('l10n_pe_einvoice.element_15_02').description.upper(), 
                                                        'element_id':self.env.ref('l10n_pe_einvoice.element_15_02').id, 'invoice_id':self.id})
                            break
                amount_tax =invoice.currency_id.round(invoice.amount_tax*(invoice.discount and (1-invoice.discount) or 1))
                amount_exonerated =invoice.currency_id.round(invoice.amount_exonerated*(invoice.discount and (1-invoice.discount) or 1.0))
                amount_untaxed =invoice.currency_id.round(invoice.amount_untaxed-amount_exonerated)
                if (amount_exonerated+amount_tax+amount_untaxed)>0:
                    amount=self.env['ir.translation'].amount_to_text_pe(invoice.currency_id.round(amount_exonerated+amount_tax+amount_untaxed) or 0, '')
                    invoice.sunat_add_line.create({'name':amount, 'element_id':self.env.ref('l10n_pe_einvoice.element_15_01').id,
                                                'invoice_id':invoice.id})
                
                if not invoice.company_id.vat:
                    raise Warning(_('The company %s need a valid VAT number!')%invoice.company_id.name)
                if not invoice.company_id.partner_id.doc_number or not invoice.company_id.partner_id.doc_type:
                    raise Warning(_('The partner %s need a valid document type and document number!') % invoice.company_id.partner_id.name)
                if not invoice.company_id.partner_id.street:
                    raise Warning(_('You must fill the address of the partner %s !') % invoice.company_id.partner_id.name)
                if not invoice.company_id.sunat_certificate:
                    raise Warning(_('You must fill the Sunat Certificate for the comapny %s !') % invoice.company_id.name)

                if not invoice.batch_pe_id:
                    invoice.batch_pe_id = self.env['einvoice.batch.pe'].create_from_invoice(invoice)
                else:
                    if invoice.batch_pe_id.state <> 'draft':
                        raise Warning(_('The electronic batch %s (id:%s) asociate to this invoice, must be in draft state')%(invoice.batch_pe_id.name,invoice.batch_pe_id.id))
                    if invoice.batch_pe_id.type <> invoice.journal_id.batch_type_pe:
                        raise Warning(_('The electronic batch %s (id:%s) asociate to this invoice, must be type %s')%(invoice.batch_pe_id.name,invoice.batch_pe_id.id,invoice.journal_id.batch_type_pe))
                    if invoice.company_id.id != invoice.batch_pe_id.company_id.id:
                        raise Warning(_('The electronic batch %s (id:%s) asociate to this invoice, must belong to the company %s')%(invoice.batch_pe_id.name,invoice.batch_pe_id.id,invoice.company_id.name))
                if invoice.batch_pe_id.type == 'sync' and invoice.company_id.sunat_see_online and invoice.batch_pe_id.state not in ['request', 'done']:
                    invoice.batch_pe_id.action_ready()
                    if invoice.journal_id.is_synchronous or invoice.sunat_payment_type=="01" or invoice.parent_id.sunat_payment_type=="01": 
                        invoice.batch_pe_id.action_request()
                elif invoice.batch_pe_id.type == 'sync' and not invoice.company_id.sunat_see_online and invoice.batch_pe_id.state not in ['request', 'done']:
                    invoice.batch_pe_id.action_ready()
        return res
    
    @api.multi
    def action_cancel(self):
        #validad por dia
        #self.batch_pe_id.action_cancel()
        return super(account_invoice,self).action_cancel()
    
    @api.multi
    def action_cancel_draft(self):
        self.batch_pe_id.action_draft()
        return super(account_invoice,self).action_cancel_draft()
    
    @api.multi
    def action_annul(self):
        self.ensure_one()
        super(account_invoice, self).action_annul()
        vals={}
        if self.journal_id.is_einvoice_pe and self.journal_id.sunat_payment_type in ['01', '03']:
            batch = self.env['einvoice.batch.pe'].search([('state', '=', 'draft'),('type','=', 'RA'),('date','=', self.date_invoice)], order='date desc')
            #hacer un excep en caso de que encuentre un resumen del dia y no este en draft
            if batch:
                vals['batch_voided_pe_id']=batch[0].id
            else:
                batch_pe_id=self.env['einvoice.batch.pe'].create({'type':'RA'})
                vals['batch_voided_pe_id']=batch_pe_id.id
            self.write(vals)
    
    @api.multi
    def get_public_cpe(self):
        self.ensure_one()
        res = {}
        (result_pdf, result_format)=report.render_report(self._cr, self._uid, self.ids, 'l10n_pe_einvoice.report_invoice', self._context)
        res['datas_sign'] =self.batch_pe_id.emessage_ids[0].xml_sign_datas
        res['datas_response'] =self.batch_pe_id.emessage_ids[0].zip_datas
        res['datas_invoice'] = result_pdf.encode('base64')
        res['name'] = "%s-%s" %(self.company_id and self.company_id.vat[2:] or "", self.batch_pe_id.name or "cpe")
        return res
    
class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'
    
    pe_affectation_code = fields.Selection(selection= "_get_pe_reason_code", string="Type of affectation", 
                                           default="10", required=True, help="Type of affectation to the IGV")
    
    @api.model
    def _get_pe_reason_code(self):
        return self.env['base.element'].get_as_selection('PE.SEE.CATALOGO_07')
    
    @api.onchange('pe_affectation_code')
    def onchange_pe_affectation_code(self):
        if self.pe_affectation_code not in ['10', '20', '30', '40']:
            if self.discount!=100:
                self.discount=100
        else:
            if self.discount==100:
                self.discount=0 
        if self.pe_affectation_code not in ['10']:
            ids = self.invoice_line_tax_id.ids
            igv_id= self.env['account.tax'].search([('tax_code_id.tax_type_pe.name', '=', '1000'), ('id', 'in', ids)])
            if igv_id:
                res= self.env['account.tax'].search([('id', 'in', ids), ('id', 'not in', igv_id.ids)]).ids
                self.invoice_line_tax_id= [(6, 0, res)]
        else:
            ids = self.invoice_line_tax_id.ids
            igv_id= self.env['account.tax'].search([('tax_code_id.tax_type_pe.name', '=', '1000'), ('id', 'in', ids)])
            if not igv_id:
                res= self.env['account.tax'].search([('tax_code_id.tax_type_pe.name', '=', '1000')])
                self.invoice_line_tax_id= [(6, 0, ids+res.ids)]
    
class account_invoice_sunat_add(models.Model):
    _name = "account.invoice.sunat.add"
    
    @api.one
    @api.depends('element_id')
    def _get_code(self):
        self.code=self.element_id.name
    
    @api.model
    def _get_sunat_add(self):
        return [('table_id','=',self.env.ref('l10n_pe_einvoice.see_catalogo_15').id)]
    
    name=fields.Char("Description", required=True)
    element_id=fields.Many2one('base.element', string="SUNAT Adds", domain=_get_sunat_add, required=True)
    code=fields.Char("Code", compute=_get_code)
    invoice_id=fields.Many2one("account.invoice", string="Invoice")
    
    @api.onchange('element_id')
    def onchange_element(self):
        if self.element_id:
            if self.env.ref('l10n_pe_einvoice.element_15_01').id==self.element_id.id:
                amount_tax =self.invoice_id.currency_id.round(self.invoice_id.amount_tax*(self.invoice_id.discount and (1-self.invoice_id.discount) or 1))
                amount_exonerated =self.invoice_id.currency_id.round(self.invoice_id.amount_exonerated*(self.invoice_id.discount and (1-self.invoice_id.discount) or 1.0))
                amount_untaxed =self.invoice_id.currency_id.round(self.invoice_id.amount_untaxed-amount_exonerated)
                amount=self.env['ir.translation'].amount_to_text_pe(self.invoice_id.currency_id.round(amount_exonerated+(amount_tax or 0)+amount_untaxed) or 0, '')
                self.name=amount
            else:
                self.name=self.element_id.description.upper()
    
        
class account_invoice_refund(models.Model):
    _inherit='account.invoice.refund'
    
    
    @api.model
    def _get_credit_note(self):
        return self.env['base.element'].get_as_selection('PE.SEE.CATALOGO_09')
    
    credit_note_type = fields.Selection(_get_credit_note, string='Credit note type', required=True, store=True)
    
    @api.multi
    def invoice_refund(self):
        res = super(account_invoice_refund,self).invoice_refund()
        if res['domain']:
            invoice_ids= len(res['domain'])>=1 and (len(res['domain'][1])>=2 and res['domain'][1][2]) or False
            if invoice_ids:
                for invoice in self.env['account.invoice'].browse(invoice_ids):
                    invoice.write({'credit_note_type': self.credit_note_type})
        return res
    