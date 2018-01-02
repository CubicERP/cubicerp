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
from openerp import _
from pysimplesoap.client import SoapClient, SoapFault
from lxml import etree as et
import convertXML
import tempfile
import zipfile
import base64
from datetime import datetime

class einvoice_batch_pe(osv.Model):
    _name = "einvoice.batch.pe"
    _inherit = "einvoice.batch"
    
    def _get_type(self, cr, uid, context=None):
        return self.pool.get('base.element').get_as_selection(cr, uid, 'PE.SEE.TIPO', context=context)
    
    def _get_status_code(self, cr, uid, context=None):
        return self.pool.get('base.element').get_as_selection(cr, uid, 'PE.SEE.ERROR', context=context)
    
    def _date(self, cr, uid, ids, fields, args, context=None):
        res = {}
        for batch in self.browse(cr, uid, ids, context=context):
            res[batch.id] = False
            for invoice in batch.invoice_ids:
                res[batch.id] = invoice.date_invoice
                continue
        return res
    
    def _status_code(self, cr, uid, ids, fields, args, context=None):
        res = {}
        for batch in self.browse(cr, uid, ids, context=context):
            res[batch.id] = False
            for message in batch.emessage_ids:
                res[batch.id] = message.status_code
                continue
        return res
    
    def _ticket_code(self, cr, uid, ids, fields, args, context=None):
        res = {}
        for batch in self.browse(cr, uid, ids, context=context):
            res[batch.id] = False
            for message in batch.emessage_ids:
                res[batch.id] = message.ticket_code
                continue
        return res
    
    def _invoice_id(self, cr, uid, ids, fields, args, context=None):
        res = {}
        for batch in self.browse(cr, uid, ids, context=context):
            res[batch.id] = False
            for invoice in batch.invoice_ids:
                res[batch.id] = invoice.id
                continue
        return res
    
    def _name_unique(self, cr, uid, ids, context=None):
        for batch in self.browse(cr, uid, ids, context=context):
            if batch.name and batch.name <> '/':
                if len(self.search(cr, uid, [('company_id','=',batch.company_id.id),
                                      ('name','=',batch.name)], context=context)) > 1:
                    return False
        return True
    
    def _get_digest(self, cr, uid, ids, fields, args, context=None):
        res = {}
        for batch in self.browse(cr, uid, ids, context=context):
            res[batch.id] = False
            for message in batch.emessage_ids:
                if message.digest:
                    res[batch.id] = message.digest
                    break
        return res
    
    def _get_signature(self, cr, uid, ids, fields, args, context=None):
        res = {}
        for batch in self.browse(cr, uid, ids, context=context):
            res[batch.id] = False
            for message in batch.emessage_ids:
                if message.signature:
                    res[batch.id] = message.signature
                    break
        return res
    
    _columns = {
            'date': fields.date('Date', required=True, readonly=True, states={'draft':[('readonly',False)],}),
            #'date': fields.function(_date, string='Date', type='date'),
            'send_date': fields.datetime(string='Send Date'),
            'invoice_ids': fields.one2many('account.invoice', 'batch_pe_id', string="Invoices", readonly=True, states={'draft':[('readonly',False)],}),
            'invoice_voided_ids': fields.one2many('account.invoice', 'batch_voided_pe_id', string="Invoices", readonly=True, states={'draft':[('readonly',False)],}),
            'invoice_summary_ids': fields.one2many('account.invoice', 'batch_summary_pe_id', string="Invoices", readonly=True, states={'draft':[('readonly',False)],}),
            'emessage_ids': fields.one2many('einvoice.message.pe', 'batch_id', string="Messages", readonly=True, states={'draft':[('readonly',False)],},
                                          help="Request and response messages from the einvoice servers"),
            'type': fields.selection(_get_type, string="Type", required=True, readonly=True, states={'draft':[('readonly',False)],}),
            'status_code': fields.function(_status_code, string='Status Code', type='selection', selection=_get_status_code),
            'invoice_id': fields.function(_invoice_id, string='Invoice', type='many2one', relation='account.invoice'),
            'ticket_code': fields.function(_ticket_code, string='Ticket code', type='char'),
            'digest': fields.function(_get_digest, string='Digest', type='char'),
            'signature': fields.function(_get_signature, string='Signature', type='char'),
            'status_emessage': fields.char("Status Message"),
        }
    
    _order= "name, date desc"
    
    _defaults = {
            'name' : '/',
            'date': fields.date.context_today,
        }
    
    _constraints = [(_name_unique, _('The name of the report must be unique!'), ['company_id','name'])]
    
    def create_from_invoice(self, cr, uid, invoice, context=None):
        res = False
        vals = {}
        vals['invoice_ids'] = [(4,invoice.id)]
        if invoice.journal_id.batch_type_pe == 'sync':
            vals['type'] = invoice.journal_id.batch_type_pe
            vals['company_id'] = invoice.company_id.id
            res = self.create(cr, uid, vals, context=context)
        elif invoice.journal_id.batch_type_pe in ('RA','RC'):
            batch_ids = self.pool.get('einvoice.batch.pe').search(cr, uid, [('company_id','=',invoice.company_id.id),
                                                                            ('type','=',invoice.journal_id.batch_type_pe),
                                                                            ('date','=',invoice.date_invoice),
                                                                            ('state','=','draft')], context=context)
            if batch_ids:
                res = batch_ids[0]
                self.write(cr, uid, batch_ids, vals, context=context)
            else:
                vals['type'] = invoice.journal_id.batch_type_pe
                vals['company_id'] = invoice.company_id.id
                res = self.create(cr, uid, vals, context=context)
        return res
    
    def action_ready(self, cr, uid, ids, context=None):
        batch_ids = [(b.id, b.name) for b in self.browse(cr, uid, ids, context=context) if b.state != 'draft']
        if batch_ids:
            raise osv.except_osv(_('Data Error'),
                                 _("You can only set to ready batch in state draft, check the next batch %s") % batch_ids)
        for batch in self.browse(cr, uid, ids, context=context):
            message=self.pool.get('einvoice.message.pe')
            if batch.message_ids:
                message.unlink(cr, uid, [m.id for m in batch.emessage_ids], context=context)
            if batch.type=="RA":
                self.get_annul_invoice(cr, uid, [batch.id], context)
            elif batch.type=="RC":
                if len(batch.invoice_summary_ids)==0:
                    self.action_summary_documents(cr, uid, ids, context)
                else:
                    continue
            else:
                vals=message.get_xml_sign(cr, uid, batch, context=context)
                vals['batch_id']=batch.id
                message.create(cr, uid, vals, context=context)
        return super(einvoice_batch_pe,self).action_ready(cr, uid, ids, context=context)

    def action_refresh(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        batch_ids = [(b.id,b.name) for b in self.browse(cr, uid, ids, context=context) if b.state not in ('draft','ready')]
        if batch_ids:
            raise osv.except_osv(_('Data Error'), _("You can only refresh batch in states draft or ready, check the next batch %s")%batch_ids)
        ctx = context.copy()
        ctx['force_refresh'] = True
        return self.action_ready(cr, uid, ids, context=ctx)
    
    def action_request(self, cr, uid, ids, context=None):
        batch_ids = [(b.id, b.name) for b in self.browse(cr, uid, ids, context=context) if b.state != 'ready']
        if batch_ids:
            raise osv.except_osv(_('Data Error'),
                                 _("You can only request batch in state ready, check the next batch %s") % batch_ids)
        for batch in self.browse(cr, uid, ids, context=context):
            vals = {}
            message=self.pool.get('einvoice.message.pe')
            if batch.name=="/":
                if batch.type == 'sync':
                    for invoice in batch.invoice_ids:
                        vals['name'] = "%s-%s"%(invoice.journal_id.sunat_payment_type,invoice.number) 
                elif batch.type == 'RC':
                    vals['name'] =  self.pool.get('ir.sequence').get(cr, uid, 'einvoice.batch.rc', context=context)
                elif batch.type == 'RA':
                    vals['name'] =  self.pool.get('ir.sequence').get(cr, uid, 'einvoice.batch.ra', context=context)
            vals['send_date']= fields.datetime.context_timestamp(cr, uid, datetime.now(), context)#time.strftime('%Y-%m-%d')
            self.write(cr, uid, [batch.id], vals, context=context)
            if batch.type in ['RA', 'RC']:
                if  batch.emessage_ids:
                    message.unlink(cr, uid, [m.id for m in batch.emessage_ids], context=context)
                self.write(cr, uid, [batch.id], {'emessage_ids':[(0,0,message.get_xml_sign(cr, uid, batch, context=context))]}, context=context)
            message.send(cr, uid, batch.id, context=context)
        return super(einvoice_batch_pe,self).action_request(cr, uid, ids, context=context)
    
    def action_cancel(self, cr, uid, ids, context=None):
        for batch in self.browse(cr, uid, ids, context=context):
            for message in batch.emessage_ids:
                message.action_cancel()
        return super(einvoice_batch_pe,self).action_cancel(cr, uid, ids, context=context)
    
    def action_draft(self, cr, uid, ids, context=None):
        for batch in self.browse(cr, uid, ids, context=context):
            for message in batch.emessage_ids:
                message.action_draft()
        return super(einvoice_batch_pe,self).action_draft(cr, uid, ids, context=context)
    
    def action_check(self, cr, uid, ids, context=None):
        for batch in self.browse(cr, uid, ids, context=context):
            if batch.type=="sync": 
                for emessage_id in batch.emessage_ids:
                    vals = self.pool.get('einvoice.message.pe').get_document_status(cr, uid, [emessage_id.id], context=context)
                    self.pool.get('einvoice.message.pe').write(cr, uid, [emessage_id.id], vals, context=context)
            elif batch.type=="RC":
                for invoice_id in batch.invoice_summary_ids:
                    for emessage_id in invoice_id.batch_pe_id.emessage_ids:
                        vals = self.pool.get('einvoice.message.pe').get_document_status(cr, uid, [emessage_id.id], context=context)
                        if vals:
                            self.pool.get('einvoice.message.pe').write(cr, uid, [emessage_id.id], vals, context=context)
    
    def get_annul_invoice(self, cr, uid, ids, context=None):
        querry=[('state', '=','annul'),('journal_id.is_einvoice_pe', '=', True), 
                ('batch_voided_pe_id','=', False),]
        invoice_ids=self.pool.get('account.invoice').search(cr, uid, querry, order=None, context=None, count=False)
        for invoice_id in invoice_ids:
            #self.pool.get('account.invoice').write(cr, uid, [invoice_id], {'is_ra_send':True}, context)
            self.write(cr, uid, ids, {'invoice_voided_ids':[(4, invoice_id)]}, context=context)
    
    def action_summary_documents(self, cr, uid, ids, context=None):
        batch=self.browse(cr, uid, ids, context)
        querry=[('state', '!=','draft'),('journal_id.is_einvoice_pe', '=', True), 
                ('date_invoice', '=', batch.date), 
                "|",('sunat_payment_type', '=', '03'), ('parent_id.sunat_payment_type', '=', '03'),
                ]
        invoice_ids=self.pool.get('account.invoice').search(cr, uid, querry, order=None, context=None, count=False)
        for invoice_id in invoice_ids:
            #self.pool.get('account.invoice').write(cr, uid, [invoice_id], {'is_ra_send':True}, context)
            self.write(cr, uid, ids, {'invoice_summary_ids':[(4, invoice_id)]}, context=context)
    
    def action_response(self, cr, uid, ids, context=None):
        vals={}
        for batch in self.browse(cr, uid, ids, context=context):
            for emessage_id in batch.emessage_ids:
                msg_id=self.pool.get('einvoice.message.pe').copy(cr, uid, emessage_id.id, {}, context=context)
                vals.update(self.pool.get('einvoice.message.pe').get_ticket_status(cr, uid, batch, context))
                self.pool.get('einvoice.message.pe').write(cr, uid, [msg_id], vals, context=context)
            if batch.type=="RC":
                for invoice_id in batch.invoice_summary_ids:
                    for emessage_id in invoice_id.batch_pe_id.emessage_ids:
                        if vals.get('zip_datas'):
                            del vals['zip_datas']
                        self.pool.get('einvoice.message.pe').write(cr, uid, [emessage_id.id], vals, context=context)
                    if invoice_id.batch_pe_id.name=="/":
                        name = "%s-%s"%(invoice_id.journal_id.sunat_payment_type,invoice_id.number)
                        self.pool.get('einvoice.batch.pe').write(cr, uid, [invoice_id.batch_pe_id.id], 
                                                                  {'name': name}, context=context)
        return super(einvoice_batch_pe, self).action_response(cr, uid, ids, context)

class einvoice_message_pe(osv.Model):
    _name = "einvoice.message.pe"
    _inherit = "einvoice.message"
    
    def _get_status_code(self, cr, uid, context=None):
        return self.pool.get('base.element').get_as_selection(cr, uid, 'PE.SEE.ERROR', context=context)
    
    def _data_get(self, cr, uid, ids, name, arg, context=None):
        if context is None:
            context = {}
        result = {}
        ctx = context.copy()
        ctx['bin_size'] = False
        for attach in self.browse(cr, uid, ids, context=ctx):
            if attach.zip_datas:
                result[attach.id] = attach.zip_datas.decode('base64')
            else:
                result[attach.id] =False
        return result
    
    def _data_set(self, cr, uid, id, name, value, arg, context=None):
        # We dont handle setting data to null
        if not value:
            return True
        if context is None:
            context = {}
        attach = self.pool.get('ir.attachment')
        self.write(cr, uid, [id], {'zip_datas': value}, context=context)
        return True
    
    _columns = {
            'batch_id': fields.many2one('einvoice.batch.pe', string='Electronic Batch', readonly=True),
            'status_code': fields.selection(_get_status_code, string='Status Code', size=16, readonly=True),
            #'datas': fields.function(_data_get, fnct_inv=_data_set, string='File Content', type="binary"),
            'digest': fields.char('Digest Value'),
            'zip_datas': fields.binary('Sunat response file'),
            'zip_fname': fields.char('Filename'),
            'xml_datas': fields.binary('XML File'),
            'xml_fname': fields.char('XML File name'),
            'xml_sign_datas': fields.binary('XML Signed File'),
            'xml_sign_fname': fields.char('XML Signed File name'),
            'zip_sign_datas': fields.binary('Zip Signed File'),
            'zip_sign_fname': fields.char('Zip Signed File name'),
            'ticket_code': fields.char("Ticket code")
        }
    
    def send(self, cr, uid, batch_id, context=None):
        message_ids = self.search(cr, uid, [('batch_id','=',batch_id),('state','=','draft')], context=context)
        return self.action_send(cr, uid, message_ids, context=context)
    
    def _verify_message(self, cr, uid, ids, context=None):
        for msg in self.browse(cr, uid, ids, context=context):
            vals={}
            xml_string=msg.message or ''
            xml_datas= msg.xml_datas and base64.b64decode(msg.xml_datas) or ''
            if (xml_string and xml_datas) and xml_string !=xml_datas:
                vals.update(self.get_xml_sign(cr, uid, msg.batch_id, xml_string=xml_string, context=context))
                self.write(cr, uid, [msg.id], vals, context=context)
    
    def action_send(self, cr, uid, ids, context=None):
        batch_obj = self.pool.get('einvoice.batch.pe')
        self._verify_message(cr, uid, ids, context)
        for msg in self.browse(cr, uid, ids, context=context):
            client = self.get_client(cr, uid, msg.batch_id, context=context)
            try:
                vals={}
                if msg.batch_id.type=="sync":
                    result=client.sendBill(msg.zip_sign_fname, msg.zip_sign_datas)
                    vals['zip_datas']=result['applicationResponse']
                    vals.update(self.get_sunat_response(cr, uid, msg.zip_sign_fname, vals['zip_datas'], context))
                elif msg.batch_id.type in ["RA", "RC"]:
                    result=client.sendSummary(msg.zip_sign_fname, msg.zip_sign_datas)
                    vals['ticket_code']= result['ticket']
                self.write(cr, uid, [msg.id], vals, context=context)
            except SoapFault as e:
                if msg.batch_id.company_id.sunat_see_online:
                    errmsg = self.pool['base.element'].get_char(cr, uid, 'PE.SEE.ERROR', e.faultcode.encode('utf-8'))
                    raise osv.except_osv ('SUNAT Error',
                                'The batch %s (id:%s) have an error ({0}): {1} %s'.format(e.faultcode.encode('utf-8'),
                                                                                          e.faultstring.encode('utf-8'))%(msg.batch_id.name,str(msg.batch_id.id), errmsg))
                else:
                    self.write(cr, uid, [msg.id], {'status_code': e.faultcode.split('.')[-1]}, context=context)
            except Exception as e:
                if msg.batch_id.company_id.sunat_see_online:
                    raise osv.except_osv('SOAP Error',
                                      'The batch %s (id:%s) have an unexpected error: %s' % (
                                      msg.batch_id.name, str(msg.batch_id.id), e.message))
        return super(einvoice_message_pe, self).action_send(cr, uid, ids, context=context)
    
    def get_zip_invoice(self, cr, uid, batch_id, signature, context=None):
        #signature=message_obj.signature
        directory = tempfile.mkdtemp(suffix=batch_id.company_id.vat and batch_id.company_id.vat[2:] or '', prefix='tmp')
        file_name=(batch_id.company_id.vat and batch_id.company_id.vat[2:].encode('utf-8')) + '-'
        if batch_id.type=="sync":
            file_name+=batch_id.invoice_id.journal_id.sunat_payment_type.encode('utf-8')+'-'+batch_id.invoice_id.number.encode('utf-8')
        else:
            file_name+=batch_id.name
        directory_name=directory+'/'+file_name+'.zip'
        zf = zipfile.ZipFile(directory_name, 
                             mode='w', 
                             compression=zipfile.ZIP_DEFLATED, 
                             )
        try:
            zf.writestr(file_name+'.xml', signature)
        finally:
            zf.close()
        #with open(directory_name, "rb") as f:
        #    bytes = f.read()
        #    encoded = base64.b64encode(bytes)
        res=open(directory_name, "rb")
        encoded=res.read().encode('base64')
        res.close()
        return encoded, file_name+'.zip', file_name
    
    def get_sunat_response(self, cr, uid, file_name, zip_datas, context=None):
        vals={}
        vals['zip_fname']=file_name
        xml_response=self.get_response(cr, uid, zip_datas, 'R-'+file_name.split('.')[0]+'.xml', contex=None)
        sunat_response=et.fromstring(xml_response)
        cbc='urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'
        tag = et.QName(cbc, 'ResponseDate')
        date=sunat_response.find('.//'+tag.text)
        tag = et.QName(cbc, 'ResponseTime')
        time= sunat_response.find('.//'+tag.text)
        #if time!=-1 and date!=-1:
        #    vals['date_end']=date.text.encode('utf-8')+' '+time.text.encode('utf-8')
        #vals['date_end']=fields.datetime.context_timestamp(cr, uid, cr, datetime.now(), context)
        tag = et.QName(cbc, 'ResponseCode')
        code = sunat_response.find('.//'+tag.text)
        if code!=-1:
            vals['status_code']="%04d" % int(code.text)
            if vals['status_code']=="0000":
                vals['state']="receive"
        return vals
    
    def get_ticket_status(self, cr, uid, batch, context):
        vals = {}
        client=self.get_client(cr, uid, batch, context=context)
        try:
            status=client.getStatus(batch.ticket_code)
            vals['zip_datas']=status['status']['content']
        except SoapFault as e:
            errmsg = self.pool['base.element'].get_char(cr, uid, 'PE.SEE.ERROR', e.faultcode.encode('utf-8'))
            raise osv.except_osv('SUNAT Error',
                                 'The batch %s (id:%s) Ticket %s have an error ({0}): {1} %s'.format(
                                     e.faultcode.encode('utf-8'),
                                     e.faultstring.encode('utf-8')) % (
                                 batch.name, str(batch.id), batch.ticket_code, errmsg))
        file_name=(batch.company_id.vat and batch.company_id.vat[2:].encode('utf-8')) + '-'
        file_name+=batch.name
        vals.update(self.get_sunat_response(cr, uid, file_name+'.zip', vals['zip_datas']))
        return vals

    def ivoice_xml_element(self, cr, uid, batch, context=None):
        if batch.type == 'sync':
            if len(batch.invoice_ids) <> 1:
                raise osv.except_osv (_('Data Error'),
                       _('The synchronize mode support only one invoice, please check it!'))
        #else:
        #    if len(batch.invoice_ids) < 1:
        #        return ""
                #raise osv.except_osv (_('Data Error'),
                #       _('Include at least one invoice, please check it!'))
        
        return convertXML.get_xml(self, cr, uid, batch)
            
    def get_xml_sign(self, cr, uid, batch, xml_string=None, xml_sign=None, context=None):
        if context is None:
            context = {}
        vals={}
        vals['batch_id'] = batch.id
        if not xml_string or context.get('force_refresh', False):
            xml_string = self.ivoice_xml_element(cr, uid, batch, context=context)
        if not xml_sign or context.get('force_refresh', False):
            key_file=batch.company_id.sunat_certificate.key
            crt_file=batch.company_id.sunat_certificate.cer
            xml_sign = convertXML.sign_xml(self, xml_string, key_file, crt_file)
        zip_datas, file_name, file_name_xml=self.pool.get('einvoice.message.pe').get_zip_invoice(cr, uid, batch, xml_sign, context=context)
        ext="urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2"
        ds='http://www.w3.org/2000/09/xmldsig#'
        vals['message']=xml_string
        vals['xml_datas']=xml_string.encode('base64')
        vals['xml_fname']=file_name_xml+'.xml'
        vals['xml_sign_datas']=xml_sign.encode('base64')
        vals['xml_sign_fname']=file_name_xml+'.xml'
        vals['zip_sign_datas']=zip_datas
        vals['zip_sign_fname']=file_name
        tag = et.QName(ds, 'DigestValue')
        digest=et.fromstring(xml_sign).find('.//'+tag.text)
        if digest!=-1:
            vals['digest']= digest.text
        tag = et.QName(ds, 'SignatureValue')
        sign=et.fromstring(xml_sign).find('.//'+tag.text)
        if digest!=-1:
            vals['signature'] = sign.text
        return vals
    
    def get_client(self, cr, uid, batch, url=None, context=None):
        url = url or batch.company_id.sunat_see_server.url
        client = SoapClient(wsdl="%s?WSDL"% url, cache = None, ns="tzmed", soap_ns="soapenv", soap_server="jbossas6", trace=True)
        client['wsse:Security'] = {
                   'wsse:UsernameToken': {
                        'wsse:Username': '%s%s'%(batch.company_id.vat[2:], batch.company_id.sunat_see_server.user),
                        'wsse:Password': '%s'% (batch.company_id.sunat_see_server.password),
                        }
                    }
        return client

    def get_document_status(self, cr, uid, ids, context=None):
        url="https://www.sunat.gob.pe/ol-it-wsconscpegem/billConsultService"
        for emessage_id in self.browse(cr, uid, ids, context):
            vals={}
            state=False
            try:
                name="%s-%s"%(emessage_id.batch_id.invoice_ids[0].journal_id.sunat_payment_type,emessage_id.batch_id.invoice_ids[0].number)
                doc_name=(emessage_id.batch_id.company_id.vat and emessage_id.batch_id.company_id.vat[2:].encode('utf-8')) + '-'
                doc_name+=name
                #client={'ruc': emessage_id.batch_id.company_id.vat[2:], 
                #        'username': emessage_id.batch_id.company_id.sunat_see_server.user,
                #        'password': emessage_id.batch_id.company_id.sunat_see_server.password,
                #        'url': url,
                #    }
                #state, status=convertXML.get_status_cdr(doc_name, client)
                client= self.get_client(cr, uid, emessage_id.batch_id, url=url, context=context)
                res=doc_name.split("-")
                params = {
                    'rucComprobante': res[0],
                    'tipoComprobante': res[1],
                    'serieComprobante': res[2],
                    'numeroComprobante': res[3]
                }
                response=client.getStatusCdr(**params)
                vals['zip_datas']=response.get('statusCdr', {}).get('content', False)
                state=True
            except SoapFault as e:
                vals['status_emessage']="%s - %s" %(str(e.faultcode or ""), str(e.faultstring or ""))
                errmsg = self.pool['base.element'].get_char(cr, uid, 'PE.SEE.ERROR', e.faultcode.encode('utf-8'))
                if errmsg:
                    vals['status_emessage'] = e.faultcode.encode('utf-8')
            except Exception:
                pass
            if state and vals.get('zip_datas'):
                vals.update(self.get_sunat_response(cr, uid, doc_name+'.zip', vals['zip_datas']))
            return vals
            
            