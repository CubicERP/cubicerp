# -*- coding: utf-8 -*-
from openerp import http
import re

class WebPeCpe(http.Controller):
    @http.route('/cpe/', type='http', auth='public', website=True)
    def render_cpe_page(self, **kw):
        #http.request.httprequest.values
        if http.request.httprequest.method == 'POST':
            try:
                req=http.request.httprequest.values
                doc_type = (not req.get('doc_type') or req.get('doc_type')=="-") and False or req.get('doc_type')
                doc_number = (not req.get('doc_number') or req.get('doc_number')=="-") and False or req.get('doc_number') or False
                num=req.get('number').split("-")
                if not req.get('number', False) and not re.match(r'^(B|F){1}[A-Z0-9]{3}\-\d+$', req.get('number')):
                    return http.request.render('l10n_pe_einvoice.cpe_page_reponse', {'invoice': {'error': True}})
                if doc_number and doc_type=='1':
                    if len(doc_number)!=8:
                        return http.request.render('l10n_pe_einvoice.cpe_page_reponse', {'invoice': {'error': True}})
                journal = http.request.env['account.journal'].sudo().search([('is_einvoice_pe','=',True), ('sequence_id.prefix', '=', "%s-"%num[0]),
                                                                             ('sunat_payment_type', '=', req.get('document_type'))])
                if not journal or len(journal)>1:
                    return http.request.render('l10n_pe_einvoice.cpe_page_reponse', {'invoice': {'error': True}})
                number = str(int(num[1])).zfill(journal.sequence_id.padding)
                querry=[('sunat_payment_type', '=', req.get('document_type')), ('partner_id.doc_type', '=', doc_type),
                        ('partner_id.doc_number', '=', doc_number), ('date_invoice', '=', req.get('date_invoice')),
                        ('internal_number','=', "%s-%s" %(num[0], number)),('amount_total','=', req.get('amount_total')),
                        ('company_id.partner_id.doc_number', '=', req.get('company_ruc'))]
                invoice = http.request.env['account.invoice'].sudo().search(querry)
                if not invoice:
                    return http.request.render('l10n_pe_einvoice.cpe_page_reponse', {'invoice': {'error': True}})
                res = invoice and invoice.get_public_cpe() or {}
                return http.request.render('l10n_pe_einvoice.cpe_page_reponse', {'invoice': res})
            except Exception:
                return http.request.render('l10n_pe_einvoice.cpe_page_reponse', {'invoice': {'error': True}})
        return http.request.render('l10n_pe_einvoice.cpe_page', {})
