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
from lxml import etree
from openerp.tools.translate import _
from openerp.osv import fields, osv
import xmlsec
from collections import OrderedDict
from StringIO import StringIO
from pysimplesoap.client import SoapClient, SoapFault, fetch
from pysimplesoap.simplexml import SimpleXMLElement
import logging
log = logging.getLogger(__name__)

class Convert2XML:

    def __init__(self):
        self._cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
        self._cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
        self._ccts="urn:un:unece:uncefact:documentation:2"
        self._ds="http://www.w3.org/2000/09/xmldsig#"
        self._ext="urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2"
        self._qdt="urn:oasis:names:specification:ubl:schema:xsd:QualifiedDatatypes-2"
        self._sac="urn:sunat:names:specification:ubl:peru:schema:xsd:SunatAggregateComponents-1"
        self._udt="urn:un:unece:uncefact:data:specification:UnqualifiedDataTypesSchemaModule:2"
        self._xsi="http://www.w3.org/2001/XMLSchema-instance"
        self._root=None

    def getX509Template(self, content):
        tag = etree.QName(self._ds, 'Signature')
        signature=etree.SubElement(content, tag.text, Id="SignatureSP", nsmap={'ds':tag.namespace})
        tag = etree.QName(self._ds, 'SignedInfo')
        signed_info=etree.SubElement(signature, tag.text, nsmap={'ds':tag.namespace})
        tag = etree.QName(self._ds, 'CanonicalizationMethod')
        etree.SubElement(signed_info, tag.text, Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315", nsmap={'ds':tag.namespace})
        tag = etree.QName(self._ds, 'SignatureMethod')
        etree.SubElement(signed_info, tag.text, Algorithm="http://www.w3.org/2000/09/xmldsig#rsa-sha1", nsmap={'ds':tag.namespace})
        tag = etree.QName(self._ds, 'Reference')
        reference=etree.SubElement(signed_info, tag.text, URI="", nsmap={'ds':tag.namespace})
        tag = etree.QName(self._ds, 'Transforms')
        transforms=etree.SubElement(reference, tag.text, nsmap={'ds':tag.namespace})
        tag = etree.QName(self._ds, 'Transform')
        etree.SubElement(transforms, tag.text, Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature", nsmap={'ds':tag.namespace})
        tag = etree.QName(self._ds, 'DigestMethod')
        etree.SubElement(reference, tag.text, Algorithm="http://www.w3.org/2000/09/xmldsig#sha1", nsmap={'ds':tag.namespace})
        tag = etree.QName(self._ds, 'DigestValue')
        etree.SubElement(reference, tag.text, nsmap={'ds':tag.namespace})
        tag = etree.QName(self._ds, 'SignatureValue')
        etree.SubElement(signature, tag.text, nsmap={'ds':tag.namespace})
        tag = etree.QName(self._ds, 'KeyInfo')
        key_info=etree.SubElement(signature, tag.text, nsmap={'ds':tag.namespace})
        tag = etree.QName(self._ds, 'X509Data')
        data=etree.SubElement(key_info, tag.text, nsmap={'ds':tag.namespace})
        tag = etree.QName(self._ds, 'X509SubjectName')
        etree.SubElement(data, tag.text, nsmap={'ds':tag.namespace})
        tag = etree.QName(self._ds, 'X509Certificate')
        etree.SubElement(data, tag.text, nsmap={'ds':tag.namespace})

    def getSignature(self, batch):
        #es parte de la firma
        tag = etree.QName(self._cac, 'Signature')
        signature=etree.SubElement(self._root, tag.text, nsmap={'cac':tag.namespace})
        tag = etree.QName(self._cbc, 'ID')
        etree.SubElement(signature, tag.text, nsmap={'cbc':tag.namespace}).text='IDSignSP'
        tag = etree.QName(self._cac, 'SignatoryParty')
        party=etree.SubElement(signature, tag.text, nsmap={'cac':tag.namespace})
        tag = etree.QName(self._cac, 'PartyIdentification')
        identification=etree.SubElement(party, tag.text, nsmap={'cac':tag.namespace})
        tag = etree.QName(self._cbc, 'ID')
        etree.SubElement(identification, tag.text, nsmap={'cbc':tag.namespace}).text=batch.company_id.vat[2:]
        tag = etree.QName(self._cac, 'PartyName')
        name=etree.SubElement(party, tag.text, nsmap={'cac':tag.namespace})
        tag = etree.QName(self._cbc, 'Name')
        etree.SubElement(name, tag.text, nsmap={'cbc':tag.namespace}).text=batch.company_id.name
        tag = etree.QName(self._cac, 'DigitalSignatureAttachment')
        attachment=etree.SubElement(signature, tag.text, nsmap={'cac':tag.namespace})
        tag = etree.QName(self._cac, 'ExternalReference')
        reference=etree.SubElement(attachment, tag.text, nsmap={'cac':tag.namespace})
        tag = etree.QName(self._cbc, 'URI')
        etree.SubElement(reference, tag.text, nsmap={'cbc':tag.namespace}).text="#SignatureSP"

    def getCompany(self, batch):
        #datos de la compania
        tag = etree.QName(self._cac, 'AccountingSupplierParty')
        supplier=etree.SubElement(self._root, tag.text, nsmap={'cac':tag.namespace})
        tag = etree.QName(self._cbc, 'CustomerAssignedAccountID')
        etree.SubElement(supplier, tag.text, nsmap={'cbc':tag.namespace}).text=batch.company_id.partner_id.doc_number
        #catalogo 6
        tag = etree.QName(self._cbc, 'AdditionalAccountID')
        etree.SubElement(supplier, tag.text, nsmap={'cbc':tag.namespace}).text=batch.company_id.partner_id.doc_type
        tag = etree.QName(self._cac, 'Party')
        party=etree.SubElement(supplier, tag.text, nsmap={'cac':tag.namespace})
        if batch.company_id.comercial_name:
            tag = etree.QName(self._cac, 'PartyName')
            party_name=etree.SubElement(party, tag.text, nsmap={'cac':tag.namespace})
            tag = etree.QName(self._cbc, 'Name')
            etree.SubElement(party_name, tag.text, nsmap={'cbc':tag.namespace}).text=batch.company_id.comercial_name
        tag = etree.QName(self._cac, 'PostalAddress')
        address=etree.SubElement(party, tag.text, nsmap={'cac':tag.namespace})
        if batch.company_id.partner_id.state_id.code:
            tag = etree.QName(self._cbc, 'ID')
            etree.SubElement(address, tag.text, nsmap={'cbc':tag.namespace}).text=batch.company_id.partner_id.state_id.code[2:]
        tag = etree.QName(self._cbc, 'StreetName')
        etree.SubElement(address, tag.text, nsmap={'cbc':tag.namespace}).text=batch.company_id.partner_id.street
        if batch.company_id.partner_id.street2:
            tag = etree.QName(self._cbc, 'CitySubdivisionName')
            etree.SubElement(address, tag.text, nsmap={'cbc':tag.namespace}).text=batch.company_id.partner_id.street2
        if batch.company_id.partner_id.state_id:
            tag = etree.QName(self._cbc, 'CityName')
            etree.SubElement(address, tag.text, nsmap={'cbc':tag.namespace}).text=batch.company_id.partner_id.state_id.parent_id.parent_id.name
            tag = etree.QName(self._cbc, 'CountrySubentity')
            etree.SubElement(address, tag.text, nsmap={'cbc':tag.namespace}).text=batch.company_id.partner_id.state_id.parent_id.name
            tag = etree.QName(self._cbc, 'District')
            etree.SubElement(address, tag.text, nsmap={'cbc':tag.namespace}).text=batch.company_id.partner_id.state_id.name
        if batch.company_id.partner_id.country_id:
            tag = etree.QName(self._cac, 'Country')
            country=etree.SubElement(address, tag.text, nsmap={'cac':tag.namespace})
            tag = etree.QName(self._cbc, 'IdentificationCode')
            etree.SubElement(country, tag.text, nsmap={'cbc':tag.namespace}).text=batch.company_id.partner_id.country_id.code
        tag = etree.QName(self._cac, 'PartyLegalEntity')
        entity=etree.SubElement(party, tag.text, nsmap={'cac':tag.namespace})
        tag = etree.QName(self._cbc, 'RegistrationName')
        etree.SubElement(entity, tag.text, nsmap={'cbc':tag.namespace}).text=batch.company_id.name

    def getAdditionalInformation(self, cr, uid, batch, tax_obj, currency_obj, data, content):
        tag = etree.QName(self._sac, 'AdditionalInformation')
        information=etree.SubElement(content, tag.text, nsmap={'sac':tag.namespace})
        amount_exonerated=currency_obj.round(cr, uid, batch.invoice_id.currency_id, batch.invoice_id.amount_exonerated*(batch.invoice_id.discount and (1-batch.invoice_id.discount/100) or 1.0))
        amount_untaxed=currency_obj.round(cr, uid, batch.invoice_id.currency_id, batch.invoice_id.amount_untaxed-amount_exonerated)
        #if amount_untaxed>0:
        tag = etree.QName(self._sac, 'AdditionalMonetaryTotal')
        info_monetary=etree.SubElement(information, tag.text, nsmap={'sac':tag.namespace})
        tag = etree.QName(self._cbc, 'ID')
        #catalogo 15 opcional
        etree.SubElement(info_monetary, tag.text, nsmap={'cbc':tag.namespace}).text=data.get_object(cr, uid, 'l10n_pe_einvoice', 'element_14_01').name
        tag = etree.QName(self._cbc, 'PayableAmount')
        etree.SubElement(info_monetary, tag.text, currencyID=batch.invoice_id.currency_id.sunat_code or  batch.invoice_id.currency_id.name,
                         nsmap={'cbc':tag.namespace}).text=str(amount_untaxed)
        #evaluar element_14_02    see_catalogo_14    1002
        if  batch.invoice_id.amount_exonerated>0:
            tag = etree.QName(self._sac, 'AdditionalMonetaryTotal')
            info_monetary=etree.SubElement(information, tag.text, nsmap={'sac':tag.namespace})
            tag = etree.QName(self._cbc, 'ID')
            etree.SubElement(info_monetary, tag.text, nsmap={'cbc':tag.namespace}).text=data.get_object(cr, uid, 'l10n_pe_einvoice', 'element_14_03').name
            tag = etree.QName(self._cbc, 'PayableAmount')
            etree.SubElement(info_monetary, tag.text, currencyID=batch.invoice_id.currency_id.sunat_code or  batch.invoice_id.currency_id.name,
                             nsmap={'cbc':tag.namespace}).text=str(amount_exonerated)
#         for line in batch.invoice_id.invoice_line:
#             if not line.invoice_line_tax_id and line.discount==100:
#                 tag = etree.QName(self._sac, 'AdditionalMonetaryTotal')
#                 info_monetary=etree.SubElement(information, tag.text, nsmap={'sac':tag.namespace})
#                 tag = etree.QName(self._cbc, 'ID')
#                 etree.SubElement(info_monetary, tag.text, nsmap={'cbc':tag.namespace}).text=data.get_object(cr, uid, 'l10n_pe_einvoice', 'element_14_04').name
#                 tag = etree.QName(self._cbc, 'PayableAmount')
#                 # evaluar esto
#                 tax_lines=tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, line.price_unit, 1, product=line.product_id or None, partner=batch.invoice_id.partner_id or None)
#                 total_included=currency_obj.round(cr, uid, batch.invoice_id.currency_id, tax_lines['total_included'])
#                 etree.SubElement(info_monetary, tag.text, currencyID=batch.invoice_id.currency_id.sunat_code or  batch.invoice_id.currency_id.name,
#                                  nsmap={'cbc':tag.namespace}).text=str(total_included)


        if batch.invoice_id.amount_gift>0:
            tag = etree.QName(self._sac, 'AdditionalMonetaryTotal')
            info_monetary=etree.SubElement(information, tag.text, nsmap={'sac':tag.namespace})
            tag = etree.QName(self._cbc, 'ID')
            etree.SubElement(info_monetary, tag.text, nsmap={'cbc':tag.namespace}).text=data.get_object(cr, uid, 'l10n_pe_einvoice', 'element_14_04').name
            tag = etree.QName(self._cbc, 'PayableAmount')
            # evaluar esto
            etree.SubElement(info_monetary, tag.text, currencyID=batch.invoice_id.currency_id.sunat_code or  batch.invoice_id.currency_id.name,
                             nsmap={'cbc':tag.namespace}).text=str(batch.invoice_id.amount_gift)

        if batch.invoice_id.amount_discount>0 or batch.invoice_id.amount_disc_total>0:
            tag = etree.QName(self._sac, 'AdditionalMonetaryTotal')
            info_monetary=etree.SubElement(information, tag.text, nsmap={'sac':tag.namespace})
            tag = etree.QName(self._cbc, 'ID')
            etree.SubElement(info_monetary, tag.text, nsmap={'cbc':tag.namespace}).text=data.get_object(cr, uid, 'l10n_pe_einvoice', 'element_14_10').name
            tag = etree.QName(self._cbc, 'PayableAmount')
            etree.SubElement(info_monetary, tag.text, currencyID=batch.invoice_id.currency_id.sunat_code or  batch.invoice_id.currency_id.name,
                             nsmap={'cbc':tag.namespace}).text=str(currency_obj.round(cr, uid, batch.invoice_id.currency_id, batch.invoice_id.amount_discount+batch.invoice_id.amount_disc_total-batch.invoice_id.amount_gift))
        #if batch.invoice_id.amount_discount and batch.invoice_id.amount_discount>0:

        #analizar opciones
        for add in batch.invoice_id.sunat_add_line:
            tag = etree.QName(self._sac, 'AdditionalProperty')
            prop=etree.SubElement(information, tag.text, nsmap={'sac':tag.namespace})
            tag = etree.QName(self._cbc, 'ID')
            etree.SubElement(prop, tag.text, nsmap={'cbc':tag.namespace}).text=add.code
            tag = etree.QName(self._cbc, 'Value')
            etree.SubElement(prop, tag.text, nsmap={'cbc':tag.namespace}).text=add.name

    def getUBLVersion(self):
        tag = etree.QName(self._cbc, 'UBLVersionID')
        etree.SubElement(self._root, tag.text, nsmap={'cbc':tag.namespace}).text='2.0'
        tag = etree.QName(self._cbc, 'CustomizationID')
        etree.SubElement(self._root, tag.text, nsmap={'cbc':tag.namespace}).text='1.0'

    def getDiscrepancyResponse(self, batch):
        tag = etree.QName(self._cac, 'DiscrepancyResponse')
        discrepancy=etree.SubElement(self._root, tag.text, nsmap={'cac':tag.namespace})
        tag = etree.QName(self._cbc, 'ReferenceID')
        etree.SubElement(discrepancy, tag.text, nsmap={'cbc':tag.namespace}).text=batch.invoice_id.parent_id.number or ''
        #catalogo Nro 9 se tiene que evaluar
        tag = etree.QName(self._cbc, 'ResponseCode')
        if batch.invoice_id.type=="out_invoice":
            etree.SubElement(discrepancy, tag.text, nsmap={'cbc':tag.namespace}).text=batch.invoice_id.debit_note_type
        elif batch.invoice_id.type=="out_refund":
            etree.SubElement(discrepancy, tag.text, nsmap={'cbc':tag.namespace}).text=batch.invoice_id.credit_note_type
        tag = etree.QName(self._cbc, 'Description')
        etree.SubElement(discrepancy, tag.text, nsmap={'cbc':tag.namespace}).text=batch.invoice_id.number

    def getBillingReference(self, batch):
        tag = etree.QName(self._cac, 'BillingReference')
        reference=etree.SubElement(self._root, tag.text, nsmap={'cac':tag.namespace})
        tag = etree.QName(self._cac, 'InvoiceDocumentReference')
        invoice=etree.SubElement(reference, tag.text, nsmap={'cac':tag.namespace})
        tag = etree.QName(self._cbc, 'ID')
        etree.SubElement(invoice, tag.text, nsmap={'cbc':tag.namespace}).text=batch.invoice_id.parent_id.number or ''
        tag = etree.QName(self._cbc, 'DocumentTypeCode')
        etree.SubElement(invoice, tag.text, nsmap={'cbc':tag.namespace}).text=batch.invoice_id.parent_id.journal_id.sunat_payment_type

    def getTaxTotal(self, cr, uid, batch, currency_obj):
        tag = etree.QName(self._cac, 'TaxTotal')
        total=etree.SubElement(self._root, tag.text, nsmap={'cac':tag.namespace})
        tag = etree.QName(self._cbc, 'TaxAmount')
        amount_tax =currency_obj.round(cr, uid, batch.invoice_id.currency_id, batch.invoice_id.amount_tax*(batch.invoice_id.discount and (1-batch.invoice_id.discount/100) or 1))
        etree.SubElement(total, tag.text, currencyID=batch.invoice_id.currency_id.sunat_code or  batch.invoice_id.currency_id.name,
                         nsmap={'cbc':tag.namespace}).text=str(amount_tax)
        for tax in batch.invoice_id.tax_line:
            if not tax.tax_code_id.tax_type_pe or not tax.tax_code_id.igv_type_pe:
                raise Warning(_('You must fill the peruvian code of the tax code %s !') % tax.tax_code_id.name)
            tag = etree.QName(self._cac, 'TaxSubtotal')
            tax_subtotal=etree.SubElement(total, tag.text, nsmap={'cac':tag.namespace})
            tag = etree.QName(self._cbc, 'TaxAmount')
            # verficar esta parte - catalogo numero 5
            amount_tax_line=currency_obj.round(cr, uid, batch.invoice_id.currency_id, tax.amount*(batch.invoice_id.discount and (1-batch.invoice_id.discount/100) or 1))
            etree.SubElement(tax_subtotal, tag.text, currencyID=batch.invoice_id.currency_id.sunat_code or  batch.invoice_id.currency_id.name,
                             nsmap={'cbc':tag.namespace}).text=str(amount_tax_line)
            tag = etree.QName(self._cac, 'TaxCategory')
            category=etree.SubElement(tax_subtotal, tag.text, nsmap={'cac':tag.namespace})
            tag = etree.QName(self._cac, 'TaxScheme')
            scheme=etree.SubElement(category, tag.text, nsmap={'cac':tag.namespace})
            tag = etree.QName(self._cbc, 'ID')
            # verificar
            etree.SubElement(scheme, tag.text, nsmap={'cbc':tag.namespace}).text=tax.tax_code_id.tax_type_pe.name
            tag = etree.QName(self._cbc, 'Name')
            etree.SubElement(scheme, tag.text,
                                      nsmap={'cbc':tag.namespace}).text=tax.tax_code_id.tax_type_pe.description and tax.tax_code_id.tax_type_pe.description.split(' ')[0]
            tag = etree.QName(self._cbc, 'TaxTypeCode')
            etree.SubElement(scheme, tag.text,
                                      nsmap={'cbc':tag.namespace}).text=tax.tax_code_id.tax_type_pe.element_char
        return amount_tax

    def getLegalMonetaryTotal(self, cr, uid, batch, currency_obj, amount_tax):
        tag = etree.QName(self._cac, 'LegalMonetaryTotal')
        total=etree.SubElement(self._root, tag.text, nsmap={'cac':tag.namespace})
        if batch.invoice_id.amount_disc_total>0:
            tag = etree.QName(self._cbc, 'AllowanceTotalAmount')
            etree.SubElement(total, tag.text, currencyID=batch.invoice_id.currency_id.sunat_code or  batch.invoice_id.currency_id.name,
                         nsmap={'cbc':tag.namespace}).text=str(batch.invoice_id.amount_disc_total)
        tag = etree.QName(self._cbc, 'PayableAmount')
        amount_exonerated=currency_obj.round(cr, uid, batch.invoice_id.currency_id, batch.invoice_id.amount_exonerated*(batch.invoice_id.discount and (1-batch.invoice_id.discount/100) or 1.0))
        amount_untaxed=currency_obj.round(cr, uid, batch.invoice_id.currency_id, batch.invoice_id.amount_untaxed-amount_exonerated)
        etree.SubElement(total, tag.text, currencyID=batch.invoice_id.currency_id.sunat_code or  batch.invoice_id.currency_id.name,
                         nsmap={'cbc':tag.namespace}).text=str(currency_obj.round(cr, uid, batch.invoice_id.currency_id, amount_exonerated+(amount_tax or 0)+amount_untaxed))

    def getInvoice(self, cr, uid, batch, tax_obj, currency_obj, data, context=None):
        xmlns=etree.QName("urn:oasis:names:specification:ubl:schema:xsd:Invoice-2", 'Invoice')
        nsmap1=OrderedDict([(None, xmlns.namespace), ('cac', self._cac), ('cbc', self._cbc), ('ccts', self._ccts),
                            ('ds', self._ds), ('ext', self._ext), ('qdt', self._qdt), ('sac', self._sac), ('udt', self._udt),
                            ('xsi', self._xsi)] )
        self._root=etree.Element(xmlns.text, nsmap=nsmap1)
        tag = etree.QName(self._ext, 'UBLExtensions')
        extensions=etree.SubElement(self._root, tag.text, nsmap={'ext':tag.namespace})
        #era opcional - Leyenda
        tag = etree.QName(self._ext, 'UBLExtension')
        extension=etree.SubElement(extensions, tag.text, nsmap={'ext':tag.namespace})
        tag = etree.QName(self._ext, 'ExtensionContent')
        content=etree.SubElement(extension, tag.text, nsmap={'ext':tag.namespace})

        self.getAdditionalInformation(cr, uid, batch, tax_obj, currency_obj, data, content)
        # to sign
        #tag = etree.QName(self._ext, 'UBLExtensions')
        #extensions=etree.SubElement(self._root, tag.text, nsmap={'ext':tag.namespace})
        tag = etree.QName(self._ext, 'UBLExtension')
        extension=etree.SubElement(extensions, tag.text, nsmap={'ext':tag.namespace})
        tag = etree.QName(self._ext, 'ExtensionContent')
        content=etree.SubElement(extension, tag.text, nsmap={'ext':tag.namespace})

        #get x509 template
        self.getX509Template(content)
        self.getUBLVersion()

        tag = etree.QName(self._cbc, 'ID')
        etree.SubElement(self._root, tag.text, nsmap={'cbc':tag.namespace}).text=batch.invoice_id.internal_number or ''
        tag = etree.QName(self._cbc, 'IssueDate')
        etree.SubElement(self._root, tag.text, nsmap={'cbc':tag.namespace}).text=batch.invoice_id.date_invoice
        #catalogo numero 1 -- falta procesar
        tag = etree.QName(self._cbc, 'InvoiceTypeCode')
        etree.SubElement(self._root, tag.text, nsmap={'cbc':tag.namespace}).text=batch.invoice_id.journal_id.sunat_payment_type
        tag = etree.QName(self._cbc, 'DocumentCurrencyCode')
        etree.SubElement(self._root, tag.text, nsmap={'cbc':tag.namespace}).text=batch.invoice_id.currency_id.sunat_code or  batch.invoice_id.currency_id.name

        self.getSignature(batch)

        #datos de la compania
        self.getCompany(batch)

        tag = etree.QName(self._cac, 'AccountingCustomerParty')
        customer=etree.SubElement(self._root, tag.text, nsmap={'cac':tag.namespace})
        tag = etree.QName(self._cbc, 'CustomerAssignedAccountID')
        etree.SubElement(customer, tag.text, nsmap={'cbc':tag.namespace}).text=batch.invoice_id.partner_id.doc_number or '-'
        tag = etree.QName(self._cbc, 'AdditionalAccountID')
        etree.SubElement(customer, tag.text, nsmap={'cbc':tag.namespace}).text=batch.invoice_id.partner_id.doc_type or '-'
        tag = etree.QName(self._cac, 'Party')
        party=etree.SubElement(customer, tag.text, nsmap={'cac':tag.namespace})
        tag = etree.QName(self._cac, 'PartyLegalEntity')
        entity=etree.SubElement(party, tag.text, nsmap={'cac':tag.namespace})
        tag = etree.QName(self._cbc, 'RegistrationName')
        etree.SubElement(entity, tag.text, nsmap={'cbc':tag.namespace}).text=batch.invoice_id.partner_id.name or '-'

        amount_tax=self.getTaxTotal(cr, uid, batch, currency_obj)
        self.getLegalMonetaryTotal(cr, uid, batch, currency_obj, amount_tax)

        cont=1
        for line in batch.invoice_id.invoice_line:
            if line.price_subtotal<0:
                continue
            tag = etree.QName(self._cac, 'InvoiceLine')
            inv_line=etree.SubElement(self._root, tag.text, nsmap={'cac':tag.namespace})
            tag = etree.QName(self._cbc, 'ID')
            etree.SubElement(inv_line, tag.text, nsmap={'cbc':tag.namespace}).text=str(cont)
            cont+=1
            tag = etree.QName(self._cbc, 'InvoicedQuantity')
            etree.SubElement(inv_line, tag.text, unitCode=line.uos_id and line.uos_id.sunat_code or 'NIU',
                             nsmap={'cbc':tag.namespace}).text=str(line.quantity)
            tag = etree.QName(self._cbc, 'LineExtensionAmount')
            etree.SubElement(inv_line, tag.text, currencyID=batch.invoice_id.currency_id.sunat_code or  batch.invoice_id.currency_id.name,
                             nsmap={'cbc':tag.namespace}).text=str(line.price_subtotal)

            tag = etree.QName(self._cac, 'PricingReference')
            pricing=etree.SubElement(inv_line, tag.text, nsmap={'cac':tag.namespace})
            tag = etree.QName(self._cac, 'AlternativeConditionPrice')
            alternative=etree.SubElement(pricing, tag.text, nsmap={'cac':tag.namespace})
            tag = etree.QName(self._cbc, 'PriceAmount')
            #evaluar si crear un modulo adicional
            #tax_obj=self.pool.get('invoice.tax')
            tax_line=tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, line.price_unit, 1, product=line.product_id or None, partner=batch.invoice_id.partner_id or None)
            total_included=currency_obj.round(cr, uid, batch.invoice_id.currency_id, tax_line['total_included'])
            etree.SubElement(alternative, tag.text, currencyID=batch.invoice_id.currency_id.sunat_code or  batch.invoice_id.currency_id.name,
                             nsmap={'cbc':tag.namespace}).text=str(line.price_unit * (1 - (line.discount or 0.0) / 100.0) and total_included)
            tag = etree.QName(self._cbc, 'PriceTypeCode')
            etree.SubElement(alternative, tag.text, nsmap={'cbc':tag.namespace}).text=data.get_object(cr, uid, 'l10n_pe_einvoice', 'element_16_1').name

            if line.discount==100 or line.price_subtotal==0:
                tag = etree.QName(self._cac, 'AlternativeConditionPrice')
                alternative=etree.SubElement(pricing, tag.text, nsmap={'cac':tag.namespace})
                tag = etree.QName(self._cbc, 'PriceAmount')
                #evaluar si crear un modulo adicional
                #tax_obj=self.pool.get('invoice.tax')
                tax_line=tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, line.price_unit, 1, product=line.product_id or None, partner=batch.invoice_id.partner_id or None)
                total_included=currency_obj.round(cr, uid, batch.invoice_id.currency_id, tax_line['total_included'])
                etree.SubElement(alternative, tag.text, currencyID=batch.invoice_id.currency_id.sunat_code or  batch.invoice_id.currency_id.name,
                                 nsmap={'cbc':tag.namespace}).text=str(total_included)
                tag = etree.QName(self._cbc, 'PriceTypeCode')
                etree.SubElement(alternative, tag.text, nsmap={'cbc':tag.namespace}).text=data.get_object(cr, uid, 'l10n_pe_einvoice', 'element_16_2').name

            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            tax_lines=tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, price, line.quantity, product=line.product_id or None, partner=batch.invoice_id.partner_id or None)
            for tax in tax_lines['taxes']:
                tag = etree.QName(self._cac, 'TaxTotal')
                total=etree.SubElement(inv_line, tag.text, nsmap={'cac':tag.namespace})
                tag = etree.QName(self._cbc, 'TaxAmount')
                etree.SubElement(total, tag.text, currencyID=batch.invoice_id.currency_id.sunat_code or  batch.invoice_id.currency_id.name,
                                 nsmap={'cbc':tag.namespace}).text=str(currency_obj.round(cr, uid, batch.invoice_id.currency_id, tax['amount']))
                tag = etree.QName(self._cac, 'TaxSubtotal')
                subtotal=etree.SubElement(total, tag.text, nsmap={'cac':tag.namespace})
                tag = etree.QName(self._cbc, 'TaxAmount')
                etree.SubElement(subtotal, tag.text, currencyID=batch.invoice_id.currency_id.sunat_code or  batch.invoice_id.currency_id.name, nsmap={'cbc':tag.namespace}).text=str(currency_obj.round(cr, uid, batch.invoice_id.currency_id, tax['amount']))
                tag = etree.QName(self._cac, 'TaxCategory')
                category=etree.SubElement(subtotal, tag.text, nsmap={'cac':tag.namespace})
                tag = etree.QName(self._cbc, 'TaxExemptionReasonCode')
                #evaluar la forma de poner estos datos podria ser desde impuestos o codigo de impuestos
                #tax_data=tax_obj.browse(cr, uid, tax[id], context)
                #catalogo 07
                etree.SubElement(category, tag.text, nsmap={'cbc':tag.namespace}).text=tax_obj.browse(cr, uid, tax['id'], context).tax_code_id.igv_type_pe
                tag = etree.QName(self._cac, 'TaxScheme')
                scheme=etree.SubElement(category, tag.text, nsmap={'cac':tag.namespace})
                tag = etree.QName(self._cbc, 'ID')
                etree.SubElement(scheme, tag.text, nsmap={'cbc':tag.namespace}).text=tax_obj.browse(cr, uid, tax['id'], context).tax_code_id.tax_type_pe.name
                tag = etree.QName(self._cbc, 'Name')
                tax_type_pe=tax_obj.browse(cr, uid, tax['id'], context).tax_code_id.tax_type_pe.description and tax_obj.browse(cr, uid, tax['id'], context).tax_code_id.tax_type_pe.description.split(' ')[0] or ''
                etree.SubElement(scheme, tag.text, nsmap={'cbc':tag.namespace}).text= tax_type_pe
                tag = etree.QName(self._cbc, 'TaxTypeCode')
                etree.SubElement(scheme, tag.text, nsmap={'cbc':tag.namespace}).text=tax_obj.browse(cr, uid, tax['id'], context).tax_code_id.tax_type_pe.element_char

            if not tax_lines['taxes'] and line.discount<100:
                tag = etree.QName(self._cac, 'TaxTotal')
                total=etree.SubElement(inv_line, tag.text, nsmap={'cac':tag.namespace})
                tag = etree.QName(self._cbc, 'TaxAmount')
                etree.SubElement(total, tag.text, currencyID=batch.invoice_id.currency_id.sunat_code or  batch.invoice_id.currency_id.name,
                                 nsmap={'cbc':tag.namespace}).text=str(0.00)
                tag = etree.QName(self._cac, 'TaxSubtotal')
                subtotal=etree.SubElement(total, tag.text, nsmap={'cac':tag.namespace})
                tag = etree.QName(self._cbc, 'TaxAmount')
                etree.SubElement(subtotal, tag.text, currencyID=batch.invoice_id.currency_id.sunat_code or  batch.invoice_id.currency_id.name,
                                 nsmap={'cbc':tag.namespace}).text=str(0.00)
                tag = etree.QName(self._cac, 'TaxCategory')
                category=etree.SubElement(subtotal, tag.text, nsmap={'cac':tag.namespace})
                tag = etree.QName(self._cbc, 'TaxExemptionReasonCode')
                etree.SubElement(category, tag.text, nsmap={'cbc':tag.namespace}).text=data.get_object(cr, uid, 'l10n_pe_einvoice', 'element_07_8').name
                tag = etree.QName(self._cac, 'TaxScheme')
                scheme=etree.SubElement(category, tag.text, nsmap={'cac':tag.namespace})
                tag = etree.QName(self._cbc, 'ID')
                etree.SubElement(scheme, tag.text, nsmap={'cbc':tag.namespace}).text= data.get_object(cr, uid, 'l10n_pe_einvoice', 'element_05_1').name
                tag = etree.QName(self._cbc, 'Name')
                etree.SubElement(scheme, tag.text, nsmap={'cbc':tag.namespace}).text= data.get_object(cr, uid, 'l10n_pe_einvoice', 'element_05_1').description.split(' ')[0]
                tag = etree.QName(self._cbc, 'TaxTypeCode')
                etree.SubElement(scheme, tag.text, nsmap={'cbc':tag.namespace}).text= data.get_object(cr, uid, 'l10n_pe_einvoice', 'element_05_1').element_char
            if not tax_lines['taxes'] and line.discount==100:
                tag = etree.QName(self._cac, 'TaxTotal')
                total=etree.SubElement(inv_line, tag.text, nsmap={'cac':tag.namespace})
                tag = etree.QName(self._cbc, 'TaxAmount')
                etree.SubElement(total, tag.text, currencyID=batch.invoice_id.currency_id.sunat_code or  batch.invoice_id.currency_id.name,
                                 nsmap={'cbc':tag.namespace}).text=str(0.00)
                tag = etree.QName(self._cac, 'TaxSubtotal')
                subtotal=etree.SubElement(total, tag.text, nsmap={'cac':tag.namespace})
                tag = etree.QName(self._cbc, 'TaxAmount')
                etree.SubElement(subtotal, tag.text, currencyID=batch.invoice_id.currency_id.sunat_code or  batch.invoice_id.currency_id.name,
                                 nsmap={'cbc':tag.namespace}).text=str(0.00)
                tag = etree.QName(self._cac, 'TaxCategory')
                category=etree.SubElement(subtotal, tag.text, nsmap={'cac':tag.namespace})
                tag = etree.QName(self._cbc, 'TaxExemptionReasonCode')
                etree.SubElement(category, tag.text, nsmap={'cbc':tag.namespace}).text=data.get_object(cr, uid, 'l10n_pe_einvoice', 'element_07_10').name
                tag = etree.QName(self._cac, 'TaxScheme')
                scheme=etree.SubElement(category, tag.text, nsmap={'cac':tag.namespace})
                tag = etree.QName(self._cbc, 'ID')
                etree.SubElement(scheme, tag.text, nsmap={'cbc':tag.namespace}).text= data.get_object(cr, uid, 'l10n_pe_einvoice', 'element_05_1').name
                tag = etree.QName(self._cbc, 'Name')
                etree.SubElement(scheme, tag.text, nsmap={'cbc':tag.namespace}).text= data.get_object(cr, uid, 'l10n_pe_einvoice', 'element_05_1').description.split(' ')[0]
                tag = etree.QName(self._cbc, 'TaxTypeCode')
                etree.SubElement(scheme, tag.text, nsmap={'cbc':tag.namespace}).text= data.get_object(cr, uid, 'l10n_pe_einvoice', 'element_05_1').element_char

            tag = etree.QName(self._cac, 'Item')
            item=etree.SubElement(inv_line, tag.text, nsmap={'cac':tag.namespace})
            tag = etree.QName(self._cbc, 'Description')
            # verificar
            etree.SubElement(item, tag.text, nsmap={'cbc':tag.namespace}).text=line.name
            if line.product_id:
                tag = etree.QName(self._cac, 'SellersItemIdentification')
                identification=etree.SubElement(item, tag.text, nsmap={'cac':tag.namespace})
                tag = etree.QName(self._cbc, 'ID')
                etree.SubElement(identification, tag.text, nsmap={'cbc':tag.namespace}).text=line.product_id and line.product_id.default_code or ''
            tag = etree.QName(self._cac, 'Price')
            price=etree.SubElement(inv_line, tag.text, nsmap={'cac':tag.namespace})
            tag = etree.QName(self._cbc, 'PriceAmount')
            tax_lines=tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, line.price_unit, 1, product=line.product_id or None, partner=batch.invoice_id.partner_id or None)
            total_untaxed=currency_obj.round(cr, uid, batch.invoice_id.currency_id, tax_lines['total'])
            etree.SubElement(price, tag.text, currencyID=batch.invoice_id.currency_id.sunat_code or  batch.invoice_id.currency_id.name,
                             nsmap={'cbc':tag.namespace}).text=str(total_untaxed)

        xml_str = etree.tostring(self._root, pretty_print=True, xml_declaration = True, encoding='utf-8', standalone=False)
        return xml_str


    def getCreditNote(self, cr, uid, batch, tax_obj, currency_obj, data, context=None):
        xmlns=etree.QName("urn:oasis:names:specification:ubl:schema:xsd:CreditNote-2", 'CreditNote')
        nsmap1=OrderedDict([(None, xmlns.namespace), ('cac', self._cac), ('cbc', self._cbc), ('ccts', self._ccts),
                            ('ds', self._ds), ('ext', self._ext), ('qdt', self._qdt), ('sac', self._sac), ('udt', self._udt),
                            ('xsi', self._xsi)] )
        self._root=etree.Element(xmlns.text, nsmap=nsmap1)
        tag = etree.QName(self._ext, 'UBLExtensions')
        extensions=etree.SubElement(self._root, tag.text, nsmap={'ext':tag.namespace})
        #era opcional - Leyenda
        tag = etree.QName(self._ext, 'UBLExtension')
        extension=etree.SubElement(extensions, tag.text, nsmap={'ext':tag.namespace})
        tag = etree.QName(self._ext, 'ExtensionContent')
        content=etree.SubElement(extension, tag.text, nsmap={'ext':tag.namespace})
        self.getAdditionalInformation(cr, uid, batch, tax_obj, currency_obj, data, content)

        tag = etree.QName(self._ext, 'UBLExtension')
        extension=etree.SubElement(extensions, tag.text, nsmap={'ext':tag.namespace})
        tag = etree.QName(self._ext, 'ExtensionContent')
        content=etree.SubElement(extension, tag.text, nsmap={'ext':tag.namespace})

        #get x509 template
        self.getX509Template(content)
        self.getUBLVersion()

        tag = etree.QName(self._cbc, 'ID')
        etree.SubElement(self._root, tag.text, nsmap={'cbc':tag.namespace}).text=batch.invoice_id.number or ''
        tag = etree.QName(self._cbc, 'IssueDate')
        etree.SubElement(self._root, tag.text, nsmap={'cbc':tag.namespace}).text=batch.invoice_id.date_invoice
        tag = etree.QName(self._cbc, 'DocumentCurrencyCode')
        etree.SubElement(self._root, tag.text, nsmap={'cbc':tag.namespace}).text=batch.invoice_id.currency_id.sunat_code or  batch.invoice_id.currency_id.name

        self.getDiscrepancyResponse(batch)

        self.getBillingReference(batch)
        #parte de la firma digital
        self.getSignature(batch)

        #datos de la compania
        self.getCompany(batch)

        tag = etree.QName(self._cac, 'AccountingCustomerParty')
        customer=etree.SubElement(self._root, tag.text, nsmap={'cac':tag.namespace})
        tag = etree.QName(self._cbc, 'CustomerAssignedAccountID')
        etree.SubElement(customer, tag.text, nsmap={'cbc':tag.namespace}).text=batch.invoice_id.partner_id.doc_number or '-'
        tag = etree.QName(self._cbc, 'AdditionalAccountID')
        etree.SubElement(customer, tag.text, nsmap={'cbc':tag.namespace}).text=batch.invoice_id.partner_id.doc_type or '-'
        tag = etree.QName(self._cac, 'Party')
        party=etree.SubElement(customer, tag.text, nsmap={'cac':tag.namespace})
        tag = etree.QName(self._cac, 'PartyLegalEntity')
        entity=etree.SubElement(party, tag.text, nsmap={'cac':tag.namespace})
        tag = etree.QName(self._cbc, 'RegistrationName')
        etree.SubElement(entity, tag.text, nsmap={'cbc':tag.namespace}).text=batch.invoice_id.partner_id.name or '-'

        amount_tax=self.getTaxTotal(cr, uid, batch, currency_obj)

        tag = etree.QName(self._cac, 'LegalMonetaryTotal')
        total=etree.SubElement(self._root, tag.text, nsmap={'cac':tag.namespace})
        tag = etree.QName(self._cbc, 'PayableAmount')
        amount_exonerated=currency_obj.round(cr, uid, batch.invoice_id.currency_id, batch.invoice_id.amount_exonerated*(batch.invoice_id.discount and (1-batch.invoice_id.discount/100) or 1.0))
        amount_untaxed=currency_obj.round(cr, uid, batch.invoice_id.currency_id, batch.invoice_id.amount_untaxed-amount_exonerated)
        etree.SubElement(total, tag.text, currencyID=batch.invoice_id.currency_id.sunat_code or  batch.invoice_id.currency_id.name,
                         nsmap={'cbc':tag.namespace}).text=str(currency_obj.round(cr, uid, batch.invoice_id.currency_id, amount_exonerated+amount_tax+amount_untaxed))

        cont=1
        for line in batch.invoice_id.invoice_line:
            tag = etree.QName(self._cac, 'CreditNoteLine')
            inv_line=etree.SubElement(self._root, tag.text, nsmap={'cac':tag.namespace})
            tag = etree.QName(self._cbc, 'ID')
            etree.SubElement(inv_line, tag.text, nsmap={'cbc':tag.namespace}).text=str(cont)
            cont+=1
            tag = etree.QName(self._cbc, 'CreditedQuantity')
            etree.SubElement(inv_line, tag.text, unitCode=line.uos_id and line.uos_id.sunat_code or 'NIU',
                             nsmap={'cbc':tag.namespace}).text=str(line.quantity)
            tag = etree.QName(self._cbc, 'LineExtensionAmount')
            etree.SubElement(inv_line, tag.text, currencyID=batch.invoice_id.currency_id.sunat_code or  batch.invoice_id.currency_id.name,nsmap={'cbc':tag.namespace}).text=str(line.price_subtotal)

            tag = etree.QName(self._cac, 'PricingReference')
            pricing=etree.SubElement(inv_line, tag.text, nsmap={'cac':tag.namespace})
            tag = etree.QName(self._cac, 'AlternativeConditionPrice')
            alternative=etree.SubElement(pricing, tag.text, nsmap={'cac':tag.namespace})
            tag = etree.QName(self._cbc, 'PriceAmount')
            #evaluar si crear un modulo adicional
            #tax_obj=self.pool.get('invoice.tax')
            tax_lines=tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, 1, line.quantity, product=line.product_id or None, partner=batch.invoice_id.partner_id or None)
            total_included=currency_obj.round(cr, uid, batch.invoice_id.currency_id, tax_lines['total_included'])
            etree.SubElement(alternative, tag.text, currencyID=batch.invoice_id.currency_id.sunat_code or  batch.invoice_id.currency_id.name,
                             nsmap={'cbc':tag.namespace}).text=str(total_included)
            tag = etree.QName(self._cbc, 'PriceTypeCode')
            etree.SubElement(alternative, tag.text, nsmap={'cbc':tag.namespace}).text=data.get_object(cr, uid, 'l10n_pe_einvoice', 'element_16_1').name
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            tax_lines=tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, price, line.quantity, product=line.product_id or None, partner=batch.invoice_id.partner_id or None)
            for tax in tax_lines['taxes']:
                tag = etree.QName(self._cac, 'TaxTotal')
                total=etree.SubElement(inv_line, tag.text, nsmap={'cac':tag.namespace})
                tag = etree.QName(self._cbc, 'TaxAmount')
                etree.SubElement(total, tag.text, currencyID=batch.invoice_id.currency_id.sunat_code or  batch.invoice_id.currency_id.name, nsmap={'cbc':tag.namespace}).text=str(currency_obj.round(cr, uid, batch.invoice_id.currency_id, tax['amount']))
                tag = etree.QName(self._cac, 'TaxSubtotal')
                subtotal=etree.SubElement(total, tag.text, nsmap={'cac':tag.namespace})
                tag = etree.QName(self._cbc, 'TaxAmount')
                etree.SubElement(subtotal, tag.text, currencyID=batch.invoice_id.currency_id.sunat_code or  batch.invoice_id.currency_id.name, nsmap={'cbc':tag.namespace}).text=str(currency_obj.round(cr, uid, batch.invoice_id.currency_id, tax['amount']))
                tag = etree.QName(self._cac, 'TaxCategory')
                category=etree.SubElement(subtotal, tag.text, nsmap={'cac':tag.namespace})
                tag = etree.QName(self._cbc, 'TaxExemptionReasonCode')
                #evaluar la forma de poner estos datos podria ser desde impuestos o codigo de impuestos
                #tax_data=tax_obj.browse(cr, uid, tax[id], context)
                etree.SubElement(category, tag.text, nsmap={'cbc':tag.namespace}).text=tax_obj.browse(cr, uid, tax['id'], context).ref_tax_code_id.igv_type_pe
                tag = etree.QName(self._cac, 'TaxScheme')
                scheme=etree.SubElement(category, tag.text, nsmap={'cac':tag.namespace})
                tag = etree.QName(self._cbc, 'ID')
                etree.SubElement(scheme, tag.text, nsmap={'cbc':tag.namespace}).text=tax_obj.browse(cr, uid, tax['id'], context).ref_tax_code_id.tax_type_pe.name
                tag = etree.QName(self._cbc, 'Name')
                tax_type_pe=tax_obj.browse(cr, uid, tax['id'], context).ref_tax_code_id.tax_type_pe.description and tax_obj.browse(cr, uid, tax['id'], context).ref_tax_code_id.tax_type_pe.description.split(' ')[0] or ''
                etree.SubElement(scheme, tag.text, nsmap={'cbc':tag.namespace}).text= tax_type_pe
                tag = etree.QName(self._cbc, 'TaxTypeCode')
                etree.SubElement(scheme, tag.text, nsmap={'cbc':tag.namespace}).text=tax_obj.browse(cr, uid, tax['id'], context).ref_tax_code_id.tax_type_pe.element_char

            if not tax_lines['taxes'] and line.discount<100:
                tag = etree.QName(self._cac, 'TaxTotal')
                total=etree.SubElement(inv_line, tag.text, nsmap={'cac':tag.namespace})
                tag = etree.QName(self._cbc, 'TaxAmount')
                etree.SubElement(total, tag.text, currencyID=batch.invoice_id.currency_id.sunat_code or  batch.invoice_id.currency_id.name,
                                 nsmap={'cbc':tag.namespace}).text=str(0.00)
                tag = etree.QName(self._cac, 'TaxSubtotal')
                subtotal=etree.SubElement(total, tag.text, nsmap={'cac':tag.namespace})
                tag = etree.QName(self._cbc, 'TaxAmount')
                etree.SubElement(subtotal, tag.text, currencyID=batch.invoice_id.currency_id.sunat_code or  batch.invoice_id.currency_id.name,
                                 nsmap={'cbc':tag.namespace}).text=str(0.00)
                tag = etree.QName(self._cac, 'TaxCategory')
                category=etree.SubElement(subtotal, tag.text, nsmap={'cac':tag.namespace})
                tag = etree.QName(self._cbc, 'TaxExemptionReasonCode')
                etree.SubElement(category, tag.text, nsmap={'cbc':tag.namespace}).text=data.get_object(cr, uid, 'l10n_pe_einvoice', 'element_07_8').name
                tag = etree.QName(self._cac, 'TaxScheme')
                scheme=etree.SubElement(category, tag.text, nsmap={'cac':tag.namespace})
                tag = etree.QName(self._cbc, 'ID')
                etree.SubElement(scheme, tag.text, nsmap={'cbc':tag.namespace}).text= data.get_object(cr, uid, 'l10n_pe_einvoice', 'element_05_1').name
                tag = etree.QName(self._cbc, 'Name')
                etree.SubElement(scheme, tag.text, nsmap={'cbc':tag.namespace}).text= data.get_object(cr, uid, 'l10n_pe_einvoice', 'element_05_1').description.split(' ')[0]
                tag = etree.QName(self._cbc, 'TaxTypeCode')
                etree.SubElement(scheme, tag.text, nsmap={'cbc':tag.namespace}).text= data.get_object(cr, uid, 'l10n_pe_einvoice', 'element_05_1').element_char
            if not tax_lines['taxes'] and line.discount==100:
                tag = etree.QName(self._cac, 'TaxTotal')
                total=etree.SubElement(inv_line, tag.text, nsmap={'cac':tag.namespace})
                tag = etree.QName(self._cbc, 'TaxAmount')
                etree.SubElement(total, tag.text, currencyID=batch.invoice_id.currency_id.sunat_code or  batch.invoice_id.currency_id.name,
                                 nsmap={'cbc':tag.namespace}).text=str(0.00)
                tag = etree.QName(self._cac, 'TaxSubtotal')
                subtotal=etree.SubElement(total, tag.text, nsmap={'cac':tag.namespace})
                tag = etree.QName(self._cbc, 'TaxAmount')
                etree.SubElement(subtotal, tag.text, currencyID=batch.invoice_id.currency_id.sunat_code or  batch.invoice_id.currency_id.name,
                                 nsmap={'cbc':tag.namespace}).text=str(0.00)
                tag = etree.QName(self._cac, 'TaxCategory')
                category=etree.SubElement(subtotal, tag.text, nsmap={'cac':tag.namespace})
                tag = etree.QName(self._cbc, 'TaxExemptionReasonCode')
                etree.SubElement(category, tag.text, nsmap={'cbc':tag.namespace}).text=data.get_object(cr, uid, 'l10n_pe_einvoice', 'element_07_10').name
                tag = etree.QName(self._cac, 'TaxScheme')
                scheme=etree.SubElement(category, tag.text, nsmap={'cac':tag.namespace})
                tag = etree.QName(self._cbc, 'ID')
                etree.SubElement(scheme, tag.text, nsmap={'cbc':tag.namespace}).text= data.get_object(cr, uid, 'l10n_pe_einvoice', 'element_05_1').name
                tag = etree.QName(self._cbc, 'Name')
                etree.SubElement(scheme, tag.text, nsmap={'cbc':tag.namespace}).text= data.get_object(cr, uid, 'l10n_pe_einvoice', 'element_05_1').description.split(' ')[0]
                tag = etree.QName(self._cbc, 'TaxTypeCode')
                etree.SubElement(scheme, tag.text, nsmap={'cbc':tag.namespace}).text= data.get_object(cr, uid, 'l10n_pe_einvoice', 'element_05_1').element_char


            tag = etree.QName(self._cac, 'Item')
            item=etree.SubElement(inv_line, tag.text, nsmap={'cac':tag.namespace})
            tag = etree.QName(self._cbc, 'Description')
            # verificar
            etree.SubElement(item, tag.text, nsmap={'cbc':tag.namespace}).text=line.name
            if line.product_id:
                tag = etree.QName(self._cac, 'SellersItemIdentification')
                identification=etree.SubElement(item, tag.text, nsmap={'cac':tag.namespace})
                tag = etree.QName(self._cbc, 'ID')
                etree.SubElement(identification, tag.text, nsmap={'cbc':tag.namespace}).text=line.product_id and line.product_id.default_code or ''
            tag = etree.QName(self._cac, 'Price')
            price=etree.SubElement(inv_line, tag.text, nsmap={'cac':tag.namespace})
            tag = etree.QName(self._cbc, 'PriceAmount')
            tax_lines=tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, line.price_unit, 1, product=line.product_id or None, partner=batch.invoice_id.partner_id or None)
            total_untaxed=currency_obj.round(cr, uid, batch.invoice_id.currency_id, tax_lines['total'])
            etree.SubElement(price, tag.text, currencyID=batch.invoice_id.currency_id.sunat_code or  batch.invoice_id.currency_id.name,
                             nsmap={'cbc':tag.namespace}).text=str(total_untaxed)

        xml_str = etree.tostring(self._root, pretty_print=True, xml_declaration = True, encoding='utf-8', standalone=False)
        return xml_str

    def getDebitNote(self, cr, uid, batch, tax_obj, currency_obj, data, context=None):
        xmlns=etree.QName("urn:oasis:names:specification:ubl:schema:xsd:DebitNote-2", 'DebitNote')
        nsmap1=OrderedDict([(None, xmlns.namespace), ('cac', self._cac), ('cbc', self._cbc), ('ccts', self._ccts),
                            ('ds', self._ds), ('ext', self._ext), ('qdt', self._qdt), ('sac', self._sac), ('udt', self._udt),
                            ('xsi', self._xsi)] )
        self._root=etree.Element(xmlns.text, nsmap=nsmap1)
        tag = etree.QName(self._ext, 'UBLExtensions')
        extensions=etree.SubElement(self._root, tag.text, nsmap={'ext':tag.namespace})
        #era opcional - Leyenda
        tag = etree.QName(self._ext, 'UBLExtension')
        extension=etree.SubElement(extensions, tag.text, nsmap={'ext':tag.namespace})
        tag = etree.QName(self._ext, 'ExtensionContent')
        content=etree.SubElement(extension, tag.text, nsmap={'ext':tag.namespace})

        self.getAdditionalInformation(cr, uid, batch, tax_obj, currency_obj, data, content)
        # to sign
        #tag = etree.QName(self._ext, 'UBLExtensions')
        #extensions=etree.SubElement(self._root, tag.text, nsmap={'ext':tag.namespace})
        tag = etree.QName(self._ext, 'UBLExtension')
        extension=etree.SubElement(extensions, tag.text, nsmap={'ext':tag.namespace})
        tag = etree.QName(self._ext, 'ExtensionContent')
        content=etree.SubElement(extension, tag.text, nsmap={'ext':tag.namespace})

        #get x509 template
        self.getX509Template(content)
        self.getUBLVersion()

        tag = etree.QName(self._cbc, 'ID')
        etree.SubElement(self._root, tag.text, nsmap={'cbc':tag.namespace}).text=batch.invoice_id.number or ''
        tag = etree.QName(self._cbc, 'IssueDate')
        etree.SubElement(self._root, tag.text, nsmap={'cbc':tag.namespace}).text=batch.invoice_id.date_invoice
        tag = etree.QName(self._cbc, 'DocumentCurrencyCode')
        etree.SubElement(self._root, tag.text, nsmap={'cbc':tag.namespace}).text=batch.invoice_id.currency_id.sunat_code or  batch.invoice_id.currency_id.name

        self.getDiscrepancyResponse(batch)
        self.getBillingReference(batch)
        self.getSignature(batch)
        self.getCompany(batch)

        tag = etree.QName(self._cac, 'AccountingCustomerParty')
        customer=etree.SubElement(self._root, tag.text, nsmap={'cac':tag.namespace})
        tag = etree.QName(self._cbc, 'CustomerAssignedAccountID')
        etree.SubElement(customer, tag.text, nsmap={'cbc':tag.namespace}).text=batch.invoice_id.partner_id.doc_number or '-'
        tag = etree.QName(self._cbc, 'AdditionalAccountID')
        etree.SubElement(customer, tag.text, nsmap={'cbc':tag.namespace}).text=batch.invoice_id.partner_id.doc_type or '-'
        tag = etree.QName(self._cac, 'Party')
        party=etree.SubElement(customer, tag.text, nsmap={'cac':tag.namespace})
        tag = etree.QName(self._cac, 'PartyLegalEntity')
        entity=etree.SubElement(party, tag.text, nsmap={'cac':tag.namespace})
        tag = etree.QName(self._cbc, 'RegistrationName')
        etree.SubElement(entity, tag.text, nsmap={'cbc':tag.namespace}).text=batch.invoice_id.partner_id.name or '-'
        amount_tax =currency_obj.round(cr, uid, batch.invoice_id.currency_id, batch.invoice_id.amount_tax*(batch.invoice_id.discount and (1-batch.invoice_id.discount/100) or 1))
        if amount_tax>0:
            amount_tax=self.getTaxTotal(cr, uid, batch, currency_obj)
        tag = etree.QName(self._cac, 'RequestedMonetaryTotal')
        total=etree.SubElement(self._root, tag.text, nsmap={'cac':tag.namespace})
        tag = etree.QName(self._cbc, 'PayableAmount')
        amount_exonerated=currency_obj.round(cr, uid, batch.invoice_id.currency_id, batch.invoice_id.amount_exonerated*(batch.invoice_id.discount and (1-batch.invoice_id.discount/100) or 1.0))
        amount_untaxed=currency_obj.round(cr, uid, batch.invoice_id.currency_id, batch.invoice_id.amount_untaxed-amount_exonerated)
        etree.SubElement(total, tag.text, currencyID=batch.invoice_id.currency_id.sunat_code or  batch.invoice_id.currency_id.name,
                         nsmap={'cbc':tag.namespace}).text=str(currency_obj.round(cr, uid, batch.invoice_id.currency_id, amount_exonerated+amount_tax+amount_untaxed))
        cont=1
        for line in batch.invoice_id.invoice_line:
            if line.price_subtotal<0:
                continue
            tag = etree.QName(self._cac, 'DebitNoteLine')
            inv_line=etree.SubElement(self._root, tag.text, nsmap={'cac':tag.namespace})
            tag = etree.QName(self._cbc, 'ID')
            etree.SubElement(inv_line, tag.text, nsmap={'cbc':tag.namespace}).text=str(cont)
            cont+=1
            tag = etree.QName(self._cbc, 'DebitedQuantity')
            # verifiar siempre es 1?
            etree.SubElement(inv_line, tag.text, unitCode=line.uos_id and line.uos_id.sunat_code or 'ZZ',
                             nsmap={'cbc':tag.namespace}).text=str(line.quantity)
            tag = etree.QName(self._cbc, 'LineExtensionAmount')
            etree.SubElement(inv_line, tag.text, currencyID=batch.invoice_id.currency_id.sunat_code or  batch.invoice_id.currency_id.name,
                             nsmap={'cbc':tag.namespace}).text=str(line.price_subtotal)

            tag = etree.QName(self._cac, 'PricingReference')
            pricing=etree.SubElement(inv_line, tag.text, nsmap={'cac':tag.namespace})
            tag = etree.QName(self._cac, 'AlternativeConditionPrice')
            alternative=etree.SubElement(pricing, tag.text, nsmap={'cac':tag.namespace})
            tag = etree.QName(self._cbc, 'PriceAmount')
            #evaluar si crear un modulo adicional
            #tax_obj=self.pool.get('invoice.tax')
            tax_line=tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, line.price_unit, 1, product=line.product_id or None, partner=batch.invoice_id.partner_id or None)
            total_included=currency_obj.round(cr, uid, batch.invoice_id.currency_id, tax_line['total_included'])
            etree.SubElement(alternative, tag.text, currencyID=batch.invoice_id.currency_id.sunat_code or  batch.invoice_id.currency_id.name,
                             nsmap={'cbc':tag.namespace}).text=str(line.price_unit * (1 - (line.discount or 0.0) / 100.0) and total_included)
            tag = etree.QName(self._cbc, 'PriceTypeCode')
            if line.discount==100 or line.price_subtotal==0:
                etree.SubElement(alternative, tag.text, nsmap={'cbc':tag.namespace}).text=data.get_object(cr, uid, 'l10n_pe_einvoice', 'element_16_2').name
            else:
                etree.SubElement(alternative, tag.text, nsmap={'cbc':tag.namespace}).text=data.get_object(cr, uid, 'l10n_pe_einvoice', 'element_16_1').name
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            tax_lines=tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, price, line.quantity, product=line.product_id or None, partner=batch.invoice_id.partner_id or None)
            for tax in tax_lines['taxes']:
                tag = etree.QName(self._cac, 'TaxTotal')
                total=etree.SubElement(inv_line, tag.text, nsmap={'cac':tag.namespace})
                tag = etree.QName(self._cbc, 'TaxAmount')
                etree.SubElement(total, tag.text, currencyID=batch.invoice_id.currency_id.sunat_code or  batch.invoice_id.currency_id.name,
                                 nsmap={'cbc':tag.namespace}).text=str(currency_obj.round(cr, uid, batch.invoice_id.currency_id, tax['amount']))
                tag = etree.QName(self._cac, 'TaxSubtotal')
                subtotal=etree.SubElement(total, tag.text, nsmap={'cac':tag.namespace})
                tag = etree.QName(self._cbc, 'TaxAmount')
                etree.SubElement(subtotal, tag.text, currencyID=batch.invoice_id.currency_id.sunat_code or  batch.invoice_id.currency_id.name, nsmap={'cbc':tag.namespace}).text=str(currency_obj.round(cr, uid, batch.invoice_id.currency_id, tax['amount']))
                tag = etree.QName(self._cac, 'TaxCategory')
                category=etree.SubElement(subtotal, tag.text, nsmap={'cac':tag.namespace})
                tag = etree.QName(self._cbc, 'TaxExemptionReasonCode')
                #evaluar la forma de poner estos datos podria ser desde impuestos o codigo de impuestos
                #tax_data=tax_obj.browse(cr, uid, tax[id], context)
                #catalogo 07
                etree.SubElement(category, tag.text, nsmap={'cbc':tag.namespace}).text=tax_obj.browse(cr, uid, tax['id'], context).tax_code_id.igv_type_pe
                tag = etree.QName(self._cac, 'TaxScheme')
                scheme=etree.SubElement(category, tag.text, nsmap={'cac':tag.namespace})
                tag = etree.QName(self._cbc, 'ID')
                etree.SubElement(scheme, tag.text, nsmap={'cbc':tag.namespace}).text=tax_obj.browse(cr, uid, tax['id'], context).tax_code_id.tax_type_pe.name
                tag = etree.QName(self._cbc, 'Name')
                tax_type_pe=tax_obj.browse(cr, uid, tax['id'], context).tax_code_id.tax_type_pe.description and tax_obj.browse(cr, uid, tax['id'], context).tax_code_id.tax_type_pe.description.split(' ')[0] or ''
                etree.SubElement(scheme, tag.text, nsmap={'cbc':tag.namespace}).text= tax_type_pe
                tag = etree.QName(self._cbc, 'TaxTypeCode')
                etree.SubElement(scheme, tag.text, nsmap={'cbc':tag.namespace}).text=tax_obj.browse(cr, uid, tax['id'], context).tax_code_id.tax_type_pe.element_char

            if not tax_lines['taxes'] and line.discount<100:
                tag = etree.QName(self._cac, 'TaxTotal')
                total=etree.SubElement(inv_line, tag.text, nsmap={'cac':tag.namespace})
                tag = etree.QName(self._cbc, 'TaxAmount')
                etree.SubElement(total, tag.text, currencyID=batch.invoice_id.currency_id.sunat_code or  batch.invoice_id.currency_id.name,
                                 nsmap={'cbc':tag.namespace}).text=str(0.00)
                tag = etree.QName(self._cac, 'TaxSubtotal')
                subtotal=etree.SubElement(total, tag.text, nsmap={'cac':tag.namespace})
                tag = etree.QName(self._cbc, 'TaxAmount')
                etree.SubElement(subtotal, tag.text, currencyID=batch.invoice_id.currency_id.sunat_code or  batch.invoice_id.currency_id.name,
                                 nsmap={'cbc':tag.namespace}).text=str(0.00)
                tag = etree.QName(self._cac, 'TaxCategory')
                category=etree.SubElement(subtotal, tag.text, nsmap={'cac':tag.namespace})
                tag = etree.QName(self._cbc, 'TaxExemptionReasonCode')
                etree.SubElement(category, tag.text, nsmap={'cbc':tag.namespace}).text=data.get_object(cr, uid, 'l10n_pe_einvoice', 'element_07_8').name
                tag = etree.QName(self._cac, 'TaxScheme')
                scheme=etree.SubElement(category, tag.text, nsmap={'cac':tag.namespace})
                tag = etree.QName(self._cbc, 'ID')
                etree.SubElement(scheme, tag.text, nsmap={'cbc':tag.namespace}).text= data.get_object(cr, uid, 'l10n_pe_einvoice', 'element_05_1').name
                tag = etree.QName(self._cbc, 'Name')
                etree.SubElement(scheme, tag.text, nsmap={'cbc':tag.namespace}).text= data.get_object(cr, uid, 'l10n_pe_einvoice', 'element_05_1').description.split(' ')[0]
                tag = etree.QName(self._cbc, 'TaxTypeCode')
                etree.SubElement(scheme, tag.text, nsmap={'cbc':tag.namespace}).text= data.get_object(cr, uid, 'l10n_pe_einvoice', 'element_05_1').element_char
            if not tax_lines['taxes'] and line.discount==100:
                tag = etree.QName(self._cac, 'TaxTotal')
                total=etree.SubElement(inv_line, tag.text, nsmap={'cac':tag.namespace})
                tag = etree.QName(self._cbc, 'TaxAmount')
                etree.SubElement(total, tag.text, currencyID=batch.invoice_id.currency_id.sunat_code or  batch.invoice_id.currency_id.name,
                                 nsmap={'cbc':tag.namespace}).text=str(0.00)
                tag = etree.QName(self._cac, 'TaxSubtotal')
                subtotal=etree.SubElement(total, tag.text, nsmap={'cac':tag.namespace})
                tag = etree.QName(self._cbc, 'TaxAmount')
                etree.SubElement(subtotal, tag.text, currencyID=batch.invoice_id.currency_id.sunat_code or  batch.invoice_id.currency_id.name,
                                 nsmap={'cbc':tag.namespace}).text=str(0.00)
                tag = etree.QName(self._cac, 'TaxCategory')
                category=etree.SubElement(subtotal, tag.text, nsmap={'cac':tag.namespace})
                tag = etree.QName(self._cbc, 'TaxExemptionReasonCode')
                etree.SubElement(category, tag.text, nsmap={'cbc':tag.namespace}).text=data.get_object(cr, uid, 'l10n_pe_einvoice', 'element_07_10').name
                tag = etree.QName(self._cac, 'TaxScheme')
                scheme=etree.SubElement(category, tag.text, nsmap={'cac':tag.namespace})
                tag = etree.QName(self._cbc, 'ID')
                etree.SubElement(scheme, tag.text, nsmap={'cbc':tag.namespace}).text= data.get_object(cr, uid, 'l10n_pe_einvoice', 'element_05_1').name
                tag = etree.QName(self._cbc, 'Name')
                etree.SubElement(scheme, tag.text, nsmap={'cbc':tag.namespace}).text= data.get_object(cr, uid, 'l10n_pe_einvoice', 'element_05_1').description.split(' ')[0]
                tag = etree.QName(self._cbc, 'TaxTypeCode')
                etree.SubElement(scheme, tag.text, nsmap={'cbc':tag.namespace}).text= data.get_object(cr, uid, 'l10n_pe_einvoice', 'element_05_1').element_char


            tag = etree.QName(self._cac, 'Item')
            item=etree.SubElement(inv_line, tag.text, nsmap={'cac':tag.namespace})
            tag = etree.QName(self._cbc, 'Description')
            # verificar
            etree.SubElement(item, tag.text, nsmap={'cbc':tag.namespace}).text=line.name
            if line.product_id:
                tag = etree.QName(self._cac, 'SellersItemIdentification')
                identification=etree.SubElement(item, tag.text, nsmap={'cac':tag.namespace})
                tag = etree.QName(self._cbc, 'ID')
                etree.SubElement(identification, tag.text, nsmap={'cbc':tag.namespace}).text=line.product_id and line.product_id.default_code or ''
            tag = etree.QName(self._cac, 'Price')
            price=etree.SubElement(inv_line, tag.text, nsmap={'cac':tag.namespace})
            tag = etree.QName(self._cbc, 'PriceAmount')
            tax_lines=tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, line.price_unit, 1, product=line.product_id or None, partner=batch.invoice_id.partner_id or None)
            total_untaxed=currency_obj.round(cr, uid, batch.invoice_id.currency_id, tax_lines['total'])
            etree.SubElement(price, tag.text, currencyID=batch.invoice_id.currency_id.sunat_code or  batch.invoice_id.currency_id.name,
                             nsmap={'cbc':tag.namespace}).text=str(total_untaxed)

        xml_str = etree.tostring(self._root, pretty_print=True, xml_declaration = True, encoding='utf-8', standalone=False)
        return xml_str

    def getVoidedDocuments(self, cr, uid, batch, tax_obj, currency_obj, data, context=None):
        xmlns=etree.QName("urn:sunat:names:specification:ubl:peru:schema:xsd:VoidedDocuments-1", 'VoidedDocuments')
        nsmap1=OrderedDict([(None, xmlns.namespace), ('cac', self._cac), ('cbc', self._cbc), ('ccts', self._ccts),
                            ('ds', self._ds), ('ext', self._ext), ('qdt', self._qdt), ('sac', self._sac), ('udt', self._udt),
                            ('xsi', self._xsi)] )
        self._root=etree.Element(xmlns.text, nsmap=nsmap1)
        tag = etree.QName(self._ext, 'UBLExtensions')
        extensions=etree.SubElement(self._root, tag.text, nsmap={'ext':tag.namespace})
        #era opcional - Leyenda
        # to sign
        tag = etree.QName(self._ext, 'UBLExtension')
        extension=etree.SubElement(extensions, tag.text, nsmap={'ext':tag.namespace})
        tag = etree.QName(self._ext, 'ExtensionContent')
        content=etree.SubElement(extension, tag.text, nsmap={'ext':tag.namespace})

        #get x509 template
        self.getX509Template(content)

        self.getUBLVersion()

        tag = etree.QName(self._cbc, 'ID')
        etree.SubElement(self._root, tag.text, nsmap={'cbc':tag.namespace}).text=batch.name
        tag = etree.QName(self._cbc, 'ReferenceDate')
        etree.SubElement(self._root, tag.text, nsmap={'cbc':tag.namespace}).text=batch.date
        tag = etree.QName(self._cbc, 'IssueDate')
        etree.SubElement(self._root, tag.text, nsmap={'cbc':tag.namespace}).text=batch.send_date
        self.getSignature(batch)
        self.getCompany(batch)
        cont=1
        for invoice_id in batch.invoice_voided_ids:
            tag = etree.QName(self._sac, 'VoidedDocumentsLine')
            line=etree.SubElement(self._root, tag.text, nsmap={'sac':tag.namespace})
            tag = etree.QName(self._cbc, 'LineID')
            etree.SubElement(line, tag.text, nsmap={'cbc':tag.namespace}).text=str(cont)
            cont+=1
            tag = etree.QName(self._cbc, 'DocumentTypeCode')
            etree.SubElement(line, tag.text, nsmap={'cbc':tag.namespace}).text=invoice_id.journal_id.sunat_payment_type
            tag = etree.QName(self._sac, 'DocumentSerialID')
            etree.SubElement(line, tag.text, nsmap={'sac':tag.namespace}).text=(invoice_id.number and invoice_id.number.split("-")[0]) or (invoice_id.internal_number and invoice_id.internal_number.split("-")[0]) or ''
            tag = etree.QName(self._sac, 'DocumentNumberID')
            etree.SubElement(line, tag.text, nsmap={'sac':tag.namespace}).text=invoice_id.number and invoice_id.number.split("-")[1] or (invoice_id.internal_number and invoice_id.internal_number.split("-")[1]) or ''
            tag = etree.QName(self._sac, 'VoidReasonDescription')
            etree.SubElement(line, tag.text, nsmap={'sac':tag.namespace}).text=invoice_id.comment or (invoice_id.state=='cancel' and 'Cancelado') or (invoice_id.state=='annul' and 'Anulado') or ''
        xml_str = etree.tostring(self._root, pretty_print=True, xml_declaration = True, encoding='utf-8', standalone=False)
        return xml_str

    def getSummaryDocuments(self, cr, uid, batch, tax_obj, currency_obj, data, journal_obj, invoice_obj, context=None):
        xmlns=etree.QName("urn:sunat:names:specification:ubl:peru:schema:xsd:SummaryDocuments-1", 'SummaryDocuments')
        nsmap1=OrderedDict([(None, xmlns.namespace), ('cac', self._cac), ('cbc', self._cbc), ('ds', self._ds),
                            ('ext', self._ext), ('sac', self._sac), ('xsi', self._xsi)] )
        self._root=etree.Element(xmlns.text, nsmap=nsmap1)
        tag = etree.QName(self._ext, 'UBLExtensions')
        extensions=etree.SubElement(self._root, tag.text, nsmap={'ext':tag.namespace})
        tag = etree.QName(self._ext, 'UBLExtension')
        extension=etree.SubElement(extensions, tag.text, nsmap={'ext':tag.namespace})
        tag = etree.QName(self._ext, 'ExtensionContent')
        content=etree.SubElement(extension, tag.text, nsmap={'ext':tag.namespace})

        #get x509 template
        self.getX509Template(content)
        self.getUBLVersion()

        tag = etree.QName(self._cbc, 'ID')
        etree.SubElement(self._root, tag.text, nsmap={'cbc':tag.namespace}).text=batch.name
        tag = etree.QName(self._cbc, 'ReferenceDate')
        etree.SubElement(self._root, tag.text, nsmap={'cbc':tag.namespace}).text=batch.date
        #catalogo numero 1 -- falta procesar <cbc:IssueDate>2012-06-24</cbc:IssueDate>
        tag = etree.QName(self._cbc, 'IssueDate')
        etree.SubElement(self._root, tag.text, nsmap={'cbc':tag.namespace}).text=batch.send_date

        self.getSignature(batch)

        #datos de la compania
        self.getCompany(batch)

        cr.execute("SELECT journal_id FROM account_invoice WHERE batch_summary_pe_id="+str(batch.id)+" group by journal_id")
        journal_ids=cr.fetchall()
        #journal_ids=journal_obj.search(cr, uid, [('sunat_payment_type', '=', 'RS')], context=context)
        cont=1
        for journal_id in journal_ids:
            journal_id=journal_id[0]
            taxes=[]
            summary_total=0
            summary_untaxed=0
            #evaluar esto
            summary_inaffected=0
            summary_exonerated=0
            summary_gift=0
            summary_discount =0
            taxes.append({'amount_tax_line':0, 'tax_name':'2000', 'tax_description':'ISC', 'tax_type_pe':'EXC'})
            taxes.append({'amount_tax_line':0, 'tax_name':'1000', 'tax_description':'IGV', 'tax_type_pe':'VAT'})
            taxes.append({'amount_tax_line':0, 'tax_name':'9999', 'tax_description':'OTROS', 'tax_type_pe':'OTH'})
            for invoice_id in batch.invoice_summary_ids:
                if invoice_id.journal_id.id==journal_id:
                    amount_tax =currency_obj.round(cr, uid, invoice_id.currency_id, invoice_id.amount_tax*(invoice_id.discount and (1-invoice_id.discount/100) or 1))
                    amount_exonerated=currency_obj.round(cr, uid, invoice_id.currency_id, invoice_id.amount_exonerated*(invoice_id.discount and (1-invoice_id.discount/100) or 1.0))
                    amount_untaxed=currency_obj.round(cr, uid, invoice_id.currency_id, invoice_id.amount_untaxed-amount_exonerated)
                    total=currency_obj.round(cr, uid, invoice_id.currency_id, amount_exonerated+(amount_tax or 0)+amount_untaxed)
                    summary_total+=total
                    summary_untaxed+=amount_untaxed
                    summary_exonerated+=amount_exonerated
                    summary_gift+=invoice_id.amount_gift
                    summary_discount+=invoice_id.amount_discount
                    for tax in invoice_id.tax_line:
                        amount_tax_line=currency_obj.round(cr, uid, invoice_id.currency_id, tax.amount*(invoice_id.discount and (1-invoice_id.discount/100) or 1))
                        #tax_name=tax.tax_code_id.tax_type_pe.name
                        #tax_description=tax.tax_code_id.tax_type_pe.description and tax.tax_code_id.tax_type_pe.description.split(' ')[0]
                        #tax_type_pe=tax.tax_code_id.tax_type_pe.element_char
                        for i in range(len(taxes)):
                            if taxes[i]['tax_name']==tax.tax_code_id.tax_type_pe.name:
                                taxes[i]['amount_tax_line']+=amount_tax_line

            journal=journal_obj.browse(cr, uid, journal_id, context=context)
            currency_code=journal.currency and (journal.currency.sunat_code or journal.currency.name) or (batch.company_id.currency_id.sunat_code or batch.company_id.currency_id.name)

            tag = etree.QName(self._sac, 'SummaryDocumentsLine')
            line=etree.SubElement(self._root, tag.text, nsmap={'sac':tag.namespace})
            tag = etree.QName(self._cbc, 'LineID')
            etree.SubElement(line, tag.text, nsmap={'cbc':tag.namespace}).text=str(cont)
            cont+=1
            tag = etree.QName(self._cbc, 'DocumentTypeCode')
            etree.SubElement(line, tag.text, nsmap={'cbc':tag.namespace}).text=journal.sunat_payment_type
            tag = etree.QName(self._sac, 'DocumentSerialID')
            etree.SubElement(line, tag.text, nsmap={'sac':tag.namespace}).text=journal.code
            tag = etree.QName(self._sac, 'StartDocumentNumberID')
            invoice_min=invoice_obj.search(cr, uid, [('journal_id', '=', journal_id),('batch_summary_pe_id', '=', batch.id)], order="number asc", limit=1, context=context)
            etree.SubElement(line, tag.text, nsmap={'sac':tag.namespace}).text=invoice_obj.browse(cr, uid, invoice_min, context=context)[0].number.split('-')[1]
            tag = etree.QName(self._sac, 'EndDocumentNumberID')
            invoice_max=invoice_obj.search(cr, uid, [('journal_id', '=', journal_id),('batch_summary_pe_id', '=', batch.id)], order="number desc", limit=1, context=context)
            etree.SubElement(line, tag.text, nsmap={'sac':tag.namespace}).text=invoice_obj.browse(cr, uid, invoice_max, context=context)[0].number.split('-')[1]
            tag = etree.QName(self._sac, 'TotalAmount')
            etree.SubElement(line, tag.text, currencyID=currency_code,
                             nsmap={'sac':tag.namespace}).text=str(summary_total)
            if summary_untaxed>0:
                tag = etree.QName(self._sac, 'BillingPayment')
                billing=etree.SubElement(line, tag.text, nsmap={'sac':tag.namespace})
                tag = etree.QName(self._cbc, 'PaidAmount')
                etree.SubElement(billing, tag.text, currencyID=currency_code, nsmap={'cbc':tag.namespace}).text=str(summary_untaxed)
                tag = etree.QName(self._cbc, 'InstructionID')
                etree.SubElement(billing, tag.text, nsmap={'cbc':tag.namespace}).text="01"
            if summary_inaffected>0:
                tag = etree.QName(self._sac, 'BillingPayment')
                billing=etree.SubElement(line, tag.text, nsmap={'sac':tag.namespace})
                tag = etree.QName(self._cbc, 'PaidAmount')
                etree.SubElement(billing, tag.text, currencyID=currency_code, nsmap={'cbc':tag.namespace}).text=str(summary_inaffected)
                tag = etree.QName(self._cbc, 'InstructionID')
                etree.SubElement(billing, tag.text, nsmap={'cbc':tag.namespace}).text="02"
            if summary_exonerated>0:
                tag = etree.QName(self._sac, 'BillingPayment')
                billing=etree.SubElement(line, tag.text, nsmap={'sac':tag.namespace})
                tag = etree.QName(self._cbc, 'PaidAmount')
                etree.SubElement(billing, tag.text, currencyID=currency_code, nsmap={'cbc':tag.namespace}).text=str(summary_exonerated)
                tag = etree.QName(self._cbc, 'InstructionID')
                etree.SubElement(billing, tag.text, nsmap={'cbc':tag.namespace}).text="03"

            if summary_gift>0:
                tag = etree.QName(self._sac, 'BillingPayment')
                billing=etree.SubElement(line, tag.text, nsmap={'sac':tag.namespace})
                tag = etree.QName(self._cbc, 'PaidAmount')
                etree.SubElement(billing, tag.text, currencyID=currency_code, nsmap={'cbc':tag.namespace}).text=str(summary_exonerated)
                tag = etree.QName(self._cbc, 'InstructionID')
                etree.SubElement(billing, tag.text, nsmap={'cbc':tag.namespace}).text="05"

            if summary_discount>0:
                tag = etree.QName(self._cac, 'AllowanceCharge')
                allowance=etree.SubElement(line, tag.text, nsmap={'cac':tag.namespace})
                tag = etree.QName(self._cbc, 'ChargeIndicator')
                etree.SubElement(allowance, tag.text, nsmap={'cbc':tag.namespace}).text="true"
                tag = etree.QName(self._cbc, 'Amount')
                etree.SubElement(allowance, tag.text, currencyID=currency_code, nsmap={'cbc':tag.namespace}).text=str(summary_discount)

            for tax in taxes:
                if tax['tax_name']=='9999' and tax['amount_tax_line']>0:
                    tag = etree.QName(self._cac, 'TaxTotal')
                    total=etree.SubElement(line, tag.text, nsmap={'cac':tag.namespace})
                    tag = etree.QName(self._cbc, 'TaxAmount')
                    etree.SubElement(total, tag.text, currencyID=currency_code,
                                     nsmap={'cbc':tag.namespace}).text=str(tax['amount_tax_line'])
                    tag = etree.QName(self._cac, 'TaxSubtotal')
                    tax_subtotal=etree.SubElement(total, tag.text, nsmap={'cac':tag.namespace})
                    tag = etree.QName(self._cbc, 'TotalAmount')
                    etree.SubElement(tax_subtotal, tag.text, currencyID=currency_code,
                                     nsmap={'cbc':tag.namespace}).text=str(tax['amount_tax_line'])
                    tag = etree.QName(self._cac, 'TaxCategory')
                    category=etree.SubElement(tax_subtotal, tag.text, nsmap={'cac':tag.namespace})
                    tag = etree.QName(self._cac, 'TaxScheme')
                    scheme=etree.SubElement(category, tag.text, nsmap={'cac':tag.namespace})
                    tag = etree.QName(self._cbc, 'ID')
                    etree.SubElement(scheme, tag.text, nsmap={'cbc':tag.namespace}).text=str(tax['tax_name'])
                    tag = etree.QName(self._cbc, 'Name')
                    etree.SubElement(scheme, tag.text,
                                              nsmap={'cbc':tag.namespace}).text=str(tax['tax_description'])
                    tag = etree.QName(self._cbc, 'TaxTypeCode')
                    etree.SubElement(scheme, tag.text,
                                              nsmap={'cbc':tag.namespace}).text=str(tax['tax_type_pe'])
                else:
                    tag = etree.QName(self._cac, 'TaxTotal')
                    total=etree.SubElement(line, tag.text, nsmap={'cac':tag.namespace})
                    tag = etree.QName(self._cbc, 'TaxAmount')
                    etree.SubElement(total, tag.text, currencyID=currency_code,
                                     nsmap={'cbc':tag.namespace}).text=str(tax['amount_tax_line'])
                    tag = etree.QName(self._cac, 'TaxSubtotal')
                    tax_subtotal=etree.SubElement(total, tag.text, nsmap={'cac':tag.namespace})
                    tag = etree.QName(self._cbc, 'TaxAmount')
                    etree.SubElement(tax_subtotal, tag.text, currencyID=currency_code,
                                     nsmap={'cbc':tag.namespace}).text=str(tax['amount_tax_line'])
                    tag = etree.QName(self._cac, 'TaxCategory')
                    category=etree.SubElement(tax_subtotal, tag.text, nsmap={'cac':tag.namespace})
                    tag = etree.QName(self._cac, 'TaxScheme')
                    scheme=etree.SubElement(category, tag.text, nsmap={'cac':tag.namespace})
                    tag = etree.QName(self._cbc, 'ID')
                    etree.SubElement(scheme, tag.text, nsmap={'cbc':tag.namespace}).text=str(tax['tax_name'])
                    tag = etree.QName(self._cbc, 'Name')
                    etree.SubElement(scheme, tag.text,
                                              nsmap={'cbc':tag.namespace}).text=str(tax['tax_description'])
                    tag = etree.QName(self._cbc, 'TaxTypeCode')
                    etree.SubElement(scheme, tag.text,
                                              nsmap={'cbc':tag.namespace}).text=str(tax['tax_type_pe'])
        xml_str = etree.tostring(self._root, pretty_print=True, xml_declaration = True, encoding='utf-8', standalone=False)
        return xml_str

    def sign_invoice(self, xml, key_file, crt_file):
        xml_iofile=StringIO(xml)
        root=etree.parse(xml_iofile).getroot()
        signature_node = xmlsec.tree.find_node(root, xmlsec.Node.SIGNATURE)
        assert signature_node is not None
        assert signature_node.tag.endswith(xmlsec.Node.SIGNATURE)
        ctx = xmlsec.SignatureContext()
        key = xmlsec.Key.from_memory(key_file, xmlsec.KeyFormat.PEM)
        assert key is not None
        key.load_cert_from_memory(crt_file, xmlsec.KeyFormat.PEM)
        ctx.key = key
        assert ctx.key is not None
        # Sign the template.
        ctx.sign(signature_node)
        return etree.tostring(root,  pretty_print=True, xml_declaration = True, encoding='utf-8', standalone=False)


def get_xml(self, cr, uid, batch, type=None, context=None):
    tax_obj=self.pool.get('account.tax')
    currency_obj=self.pool.get('res.currency')
    data  = self.pool.get('ir.model.data')
    xml_string=''
    xml_sign=''
    key=batch.company_id.sunat_certificate.key
    cer=batch.company_id.sunat_certificate.cer
    if batch.invoice_id.type=="out_invoice" and batch.type=="sync":
        if batch.invoice_id.sunat_payment_type=='08':
            xml_string =Convert2XML().getDebitNote(cr, uid, batch, tax_obj, currency_obj, data, context)
        else:
            xml_string =Convert2XML().getInvoice(cr, uid, batch, tax_obj, currency_obj, data, context)
    elif batch.invoice_id.type=="out_refund" and batch.type=="sync":
        xml_string =Convert2XML().getCreditNote(cr, uid, batch, tax_obj, currency_obj, data, context)
    elif batch.type=="RA":
        xml_string =Convert2XML().getVoidedDocuments(cr, uid, batch, tax_obj, currency_obj, data, context)
    elif batch.type=="RC":
        journal_obj=self.pool.get('account.journal')
        invoice_obj=self.pool.get('account.invoice')
        xml_string = Convert2XML().getSummaryDocuments(cr, uid, batch, tax_obj, currency_obj, data, journal_obj, invoice_obj, context=None)
    return xml_string

def sign_xml(self, xml_string, key_file, crt_file):
    xml_sign_string=Convert2XML().sign_invoice(xml_string.encode('utf-8'), key_file, crt_file)
    return xml_sign_string

class Client(object):

    def __init__(self, ruc, username, password, url, debug=False, type=None):
        self._username = "%s%s" %(ruc,username)
        self._password = password
        self._debug = debug
        self._url = "%s?WSDL" % url
        self._location = url
        self._namespace = url
        self._soapaction= "urn:getStatus"
        self._method = "getStatusCdr"
        self._soapenv="""<SOAP-ENV:Envelope xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <SOAP-ENV:Header xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope">
        <wsse:Security>
            <wsse:UsernameToken>
                <wsse:Username>%s</wsse:Username>
                <wsse:Password>%s</wsse:Password>
            </wsse:UsernameToken>
        </wsse:Security>
    </SOAP-ENV:Header>
    <SOAP-ENV:Body>
        %s
    </SOAP-ENV:Body>
</SOAP-ENV:Envelope>"""
        self._soap_namespaces = dict(
                                    soap11='http://schemas.xmlsoap.org/soap/envelope/',
                                    soap='http://schemas.xmlsoap.org/soap/envelope/',
                                    soapenv='http://schemas.xmlsoap.org/soap/envelope/',
                                    soap12='http://www.w3.org/2003/05/soap-env',
                                    soap12env="http://www.w3.org/2003/05/soap-envelope"
                                )
        self._exceptions = True
        self._connect()

    def _connect(self):
        self._client = SoapClient(location=self._location, action= self._soapaction, namespace=self._namespace)

    def _call_ws(self, xml):
        xml_response = self._client.send(self._method, xml)
        log.info(xml_response)
        response = SimpleXMLElement(xml_response, namespace=self._namespace,
                                    jetty=False)

        if self._exceptions and response("Fault", ns=list(self._soap_namespaces.values()), error=False):
            detailXml = response("detail", ns=list(self._soap_namespaces.values()), error=False)
            detail = None

            if detailXml and detailXml.children():
                if self.services is not None:
                    operation = self._client.get_operation(self._method)
                    fault_name = detailXml.children()[0].get_name()
                    # if fault not defined in WSDL, it could be an axis or other
                    # standard type (i.e. "hostname"), try to convert it to string
                    fault = operation['faults'].get(fault_name) or unicode
                    detail = detailXml.children()[0].unmarshall(fault, strict=False)
                else:
                    detail = repr(detailXml.children())

            raise SoapFault(unicode(response.faultcode),
                            unicode(response.faultstring),
                            detail)
        soap_uri = self._soap_namespaces['soapenv']
        resp = response('Body', ns=soap_uri).children().unmarshall(None, strict=True)
        return resp and list(resp.values())[0]


    def _call_service(self, params):
        cdr = """<m:getStatusCdr xmlns:m="http://service.sunat.gob.pe">
            <rucComprobante>%s</rucComprobante>
            <tipoComprobante>%s</tipoComprobante>
            <serieComprobante>%s</serieComprobante>
            <numeroComprobante>%s</numeroComprobante>
        </m:getStatusCdr>"""%(params['rucComprobante'],params['tipoComprobante'],params['serieComprobante'],
                              params['numeroComprobante'])
        try:
            xml=self._soapenv %(self._username, self._password, cdr)
            response = self._call_ws(xml)
            state=True
        except Exception, e:
            return False, {'faultcode': str(e.faultcode), 'faultstring': str(e.faultstring)}
        if state:
            try:
                res={'statusCdr': {'content':str(response.statusCdr.content)}}
            except Exception:
                res=  {'faultcode': str(response.statusCdr.statusCode), 'faultstring': str(response.statusCdr.statusMessage)}
                state=False
        return state, res

    def get_status_cdr(self, document_name):
        res=document_name.split("-")
        params = {
            'rucComprobante': res[0],
            'tipoComprobante': res[1],
            'serieComprobante': res[2],
            'numeroComprobante': res[3]
        }
        return self._call_service(params)


def get_status_cdr(document_name, client):
    client['url']= "https://www.sunat.gob.pe/ol-it-wsconscpegem/billConsultService"
    client = Client(**client)
    return client.get_status_cdr(document_name)
