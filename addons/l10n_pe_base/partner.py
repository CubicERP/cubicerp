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
import urllib
import urllib2
from lxml import etree
import re
from StringIO import StringIO
from PIL import Image
import requests
import pytesseract
from openerp.tools.translate import _
from collections import OrderedDict

class res_partner(osv.Model):
    _inherit = "res.partner"
    _columns = {
        'sunat_state': fields.char('Sunat State', 64, select=1, help="Must be ACTIVO, BAJA DE OFICIO, SUSPENSION TEMPORAL, ..."),
        'sunat_condition': fields.selection([('HABIDO','HABIDO'),
                                        ('NO HALLADO','NO HALLADO'),
                                        ('NO HABIDO','NO HABIDO'),('PENDIENTE', 'PENDIENTE')], 'Sunat condition'),
        'sunat_retention_agent': fields.boolean('Sunat Retention Agent'),
        'sunat_retention': fields.char('Retention Description',1024),
        'ciu_ids':fields.many2many('base.element', 'l10n_pe_ple_ciu', 'partner_id', 
                                   'base_element_id', 'Economic activities', domain="[('table_id.code','=','PE.SUNAT.CIIU')]",
                                   help="International Standard Industrial Classification"),
        'ciu_main_id': fields.many2one('base.element', 'Main economic activity', 
                                       domain="[('table_id.code','=','PE.SUNAT.CIIU')]",
                                       help="Main International Standard Industrial Classification")
#         'sunat_captcha_code': fields.char('Captcha Code',4),
#         'sunat_captcha_token': fields.text('Captcha Token'),
    }
    
#     def onchange_captcha_code(self, cr, uid, ids, doc_type, doc_number, sunat_captcha_code, sunat_captcha_token, context=None):
#         res = {'value':{},'warning':{}}
#         if doc_type=='6' and doc_number and sunat_captcha_code and sunat_captcha_token:
#             res['value'].update(self.get_company_details(cr, uid, doc_number, sunat_captcha_code, sunat_captcha_token, context=context))
#         return res

    def get_captcha(self, type):
        if type=="ruc":
            s = requests.Session()
            try:
                r = s.get('http://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/captcha?accion=image&nmagic=0')
            except requests.exceptions.RequestException as e:
                return (False,e)
            img=Image.open(StringIO(r.content))
            captcha_val=pytesseract.image_to_string(img)
            captcha_val=captcha_val.strip().upper()
            return (s, captcha_val)
        elif type == 'dni':
            s = requests.Session() 
            try:
                r = s.get('https://cel.reniec.gob.pe/valreg/codigo.do')
            except s.exceptions.RequestException as e:
                return (False,e)
            img=Image.open(StringIO(r.content))
            img = img.convert("RGBA")
            pixdata = img.load()
            for y in xrange(img.size[1]):
                for x in xrange(img.size[0]):
                    red, green, blue, alpha=pixdata[x, y]
                    if blue<100:
                        pixdata[x, y] = (255, 255, 255, 255)
            temp_captcha_val=pytesseract.image_to_string(img)
            temp_captcha_val=temp_captcha_val.strip().upper()
            captcha_val=''
            for i in range(len(temp_captcha_val)):
                if temp_captcha_val[i].isalpha() or temp_captcha_val[i].isdigit():
                    captcha_val=captcha_val+temp_captcha_val[i]
            return (s, captcha_val.upper())

    def get_company_details(self, cr, uid, ruc, context=None):
        res = {}
        if not ruc or not self.pool.get('res.company').browse(cr, uid, self.pool.get('res.users')._get_company(cr, uid, context=context), context=context).sunat_search_vat:
            return res
        for i in range(10):
            consuta,code=self.get_captcha('ruc')
            if not consuta:
                res['warning'] = {}
                res['warning']['title'] = _('Connection error')
                res['warning']['message'] = _('The server is not available! try again!')
                return res
            if code.isalpha():
                break
        payload = OrderedDict()
        payload['accion']='consPorRuc'
        payload['razSoc']=''
        payload['nroRuc']=ruc
        payload['nrodoc']=''
        payload['contexto']='ti-it'
        payload['tQuery']='on'
        payload['search1']=ruc
        payload['codigo']=code
        payload['tipdoc']='1'
        payload['search2']=''
        payload['coddpto']=''
        payload['codprov']=''
        payload['coddist']=''
        payload['search3']=''
        post = consuta.post("http://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/jcrS00Alias", params=payload)
        the_page = post.text
        the_page = the_page.replace('<br>','\n')
        the_page=re.sub("(<!--.*?-->)", "", the_page, flags=re.MULTILINE)
        parser = etree.HTMLParser()
        tree   = etree.parse(StringIO(the_page), parser)
        flag_nombre = False
        flag_direccion = False
        flag_estado = False
        flag_condicion = False
        flag_telefono = False
        flag_padrones = False
        flag_ciu = False
        for _td in tree.findall("//div[@id='print']/table//td"):
            if _td.attrib['class'] == 'bgn':
                if re.findall(re.compile('N.mero.de RUC.'), _td.text):
                    flag_nombre = True
                elif re.findall(re.compile('Direcci.n.'), _td.text):
                    flag_direccion = True
                elif re.findall(re.compile('Estado.'), _td.text):
                    flag_estado = True
                elif re.findall(re.compile('Condici.n.'), _td.text):
                    flag_condicion = True
                elif re.findall(re.compile('Tel.fono.'), _td.text):
                    flag_telefono = True
                elif re.findall(re.compile('Padrones.'), _td.text):
                    flag_padrones = True
                elif re.findall(re.compile('Actividad.es. Econ.mica.s.'), _td.text):
                    flag_ciu=True
            elif _td.attrib['class'] == 'bg':
                if flag_nombre:
                    flag_nombre = False
                    res['name'] = _td.text.split(' - ')[1]
                    names = res['name'].split('-')
                    if len(names) > 1:
                        res['name'] = names[len(names) - 1]
                    res['name'] = res['name'].replace('SOCIEDAD ANONIMA CERRADA','S.A.C.')
                    res['name'] = res['name'].replace('SOCIEDAD ANONIMA ABIERTA','S.A.A.')
                    res['name'] = res['name'].replace('SOCIEDAD ANONIMA','S.A.')
                elif flag_direccion:
                    flag_direccion = False
                    street=""
                    for temp in _td.text.strip().split(' '):
                        if temp:
                            street+=temp+" "
                    res['street'] = street.strip()
                    res['country_id'] = self.pool.get('res.country').search(cr, uid, [('code','=','PE')], context=context)[0]
                elif flag_estado:
                    flag_estado = False
                    #res['sunat_state'] = '%s - %s'%(res.get('sunat_state',''),_td.text.strip())
                    res['sunat_state'] = _td.text
                elif flag_condicion:
                    flag_condicion = False
                    res['sunat_condition'] = _td.text.strip()
                elif flag_telefono:
                    flag_telefono = False
                    res['phone'] = _td.text
                elif flag_padrones:
                    flag_padrones = False
                    if re.findall(re.compile('.Agentes de Retenci.n de IGV.'), _td.text):
                        res['sunat_retention_agent'] = True
                        res['sunat_retention'] = _td.text.strip()
                elif flag_ciu:
                    flag_ciu =False
                    ciu_ids=[]
                    
                    if _td.text and self.pool.get('base.table').search(cr, uid, [('code','=','PE.SUNAT.CIIU')], context=context):
                        cius= _td.text.strip().split("\n")
                        for ciu in cius:
                            if ciu.strip():
                                ciu_sunat=ciu.strip().split("-")
                                element_id=False
                                if self.pool.get('base.element').search(cr, uid, [('name','=',ciu_sunat[1].strip())], context=context):
                                    element_id=self.pool.get('base.element').search(cr, uid, [('name','=',ciu_sunat[1].strip())], context=context)[0]
                                else:
                                    table_id=self.pool.get('base.table').search(cr, uid, [('code','=','PE.SUNAT.CIIU')], context=context)[0]
                                    element_id=self.pool.get('base.element').create(cr, uid,{'name':ciu_sunat[1].strip(), 
                                                                                             'description':ciu_sunat[2].strip(), 'table_id': table_id})
                                if ciu_sunat[0].strip()=='Principal':
                                    res['ciu_main_id']=element_id
                                if element_id:
                                    ciu_ids.append(element_id)  
                    res['ciu_ids']=ciu_ids
        return res

    def get_partner_details(self, cr, uid, dni, context=None):
        res={}
        for i in range(10):
            consuta, captcha_val= self.get_captcha('dni')
            if not consuta:
                res['warning'] = {}
                res['warning']['title'] = _('Connection error')
                res['warning']['message'] = _('The server is not available! try again!')
                return res
            if len(captcha_val)==4:
                break
        payload={'accion': 'buscar', 'nuDni': dni, 'imagen': captcha_val}
        post = consuta.post("https://cel.reniec.gob.pe/valreg/valreg.do", params=payload)
        texto_consulta=post.text
        parser = etree.HTMLParser()
        tree   = etree.parse(StringIO(texto_consulta), parser)
        name=''
        for _td in tree.findall("//td[@class='style2']"):
            if _td.text:
                _name=_td.text.split("\n")
                for i in range(len(_name)):
                    _name[i]=_name[i].strip()
                name=' '.join(_name)
                break
        error_captcha="Ingrese el código que aparece en la imagen"
        error_dni="El DNI N°"
        if error_captcha==name.strip().encode('utf-8'):
            return self.get_partner_details(cr, uid, dni, context)
        elif error_dni==name.strip().encode('utf-8'):
            res['warning'] = {}
            res['warning']['title'] = _('Error')
            res['warning']['message'] = _('The DNI entered is incorrect')
            return res

        for _td in tree.findall("//td[@class='style2']"):
            if _td.text:
                _name=_td.text.split("\n")
                cont=0
                for i in range(len(_name)):
                    if _name[i].strip() and cont==0:
                        name1=_name[i].strip().split(' ')
                        cont+=1
                        if len(name1)>=2:
                            res['first_name']=_name[i].strip()[:len(name1[0])]
                            res['middle_name']=_name[i].strip()[len(name1[0]):].strip()
                        else:
                            res['first_name']=_name[i].strip()
                    elif  _name[i].strip() and cont==1:
                        res['surname']=_name[i].strip()
                        cont+=1
                    elif  _name[i].strip() and cont==2:
                        res['mother_name']=_name[i].strip()
                        cont+=1
                break
        #country_id=self.pool.get('res.country').search(cr, uid, [('code','=','PE')], limit=1)
        res['name']=name
        model  = self.pool.get('ir.model.data')
        country_id = model.get_object(cr, uid, 'base', 'pe').id
        res['country_id']=country_id or ''
        return res
