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
import openerp.netsvc
import datetime

class ir_translation(osv.osv):
    _name = "ir.translation"
    _inherit = 'ir.translation'

#-------------------------------------------------------------
#ENGLISH
#-------------------------------------------------------------

    def english_number(self, val):
        to_19 = ( 'Zero',  'One',   'Two',  'Three', 'Four',   'Five',   'Six',
                  'Seven', 'Eight', 'Nine', 'Ten',   'Eleven', 'Twelve', 'Thirteen',
                  'Fourteen', 'Fifteen', 'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen' )
        tens  = ( 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety')
        denom = ( '',
                  'Thousand',     'Million',         'Billion',       'Trillion',       'Quadrillion',
                  'Quintillion',  'Sextillion',      'Septillion',    'Octillion',      'Nonillion',
                  'Decillion',    'Undecillion',     'Duodecillion',  'Tredecillion',   'Quattuordecillion',
                  'Sexdecillion', 'Septendecillion', 'Octodecillion', 'Novemdecillion', 'Vigintillion' )

        # convert a value < 100 to English.
        def _convert_nn(val):
            if val < 20:
                return to_19[val]
            for (dcap, dval) in ((k, 20 + (10 * v)) for (v, k) in enumerate(tens)):
                if dval + 10 > val:
                    if val % 10:
                        return dcap + '-' + to_19[val % 10]
                    return dcap

        # convert a value < 1000 to english, special cased because it is the level that kicks 
        # off the < 100 special case.  The rest are more general.  This also allows you to
        # get strings in the form of 'forty-five hundred' if called directly.
        def _convert_nnn(val):
            word = ''
            (mod, rem) = (val % 100, val // 100)
            if rem > 0:
                word = to_19[rem] + ' Hundred'
                if mod > 0:
                    word = word + ' '
            if mod > 0:
                word = word + _convert_nn(mod)
            return word

        if val < 100:
            return _convert_nn(val)
        if val < 1000:
            return _convert_nnn(val)
        for (didx, dval) in ((v - 1, 1000 ** v) for v in range(len(denom))):
            if dval > val:
                mod = 1000 ** didx
                l = val // mod
                r = val - (l * mod)
                ret = _convert_nnn(l) + ' ' + denom[didx]
                if r > 0:
                    ret = ret + ', ' + english_number(r)
                return ret

    def amount_to_text_en(self, number, currency):
        netsvc.Logger().notifyChannel("amount_to_text_en",netsvc.LOG_INFO, "number_in: %s, currency: %s"%(number, currency))
        number = '%.2f' % number
        units_name = currency
        list = str(number).split('.')
        start_word = self.english_number(int(list[0]))
        end_word = self.english_number(int(list[1]))
        cents_number = int(list[1])
        cents_name = (cents_number > 1) and 'Cents' or 'Cent'
        final_result = start_word +' '+units_name+' and ' + end_word +' '+cents_name
        return final_result

#-------------------------------------------------------------
# Español
#-------------------------------------------------------------
    def __convertNumber(self,n):
        UNIDADES = ('','UNO ','DOS ','TRES ','CUATRO ','CINCO ','SEIS ','SIETE ','OCHO ','NUEVE ','DIEZ ',
                    'ONCE ','DOCE ','TRECE ','CATORCE ','QUINCE ','DIECISEIS ','DIECISIETE ','DIECIOCHO ','DIECINUEVE ','VEINTE ')                 
        DECENAS = ('VENTI','TREINTA ','CUARENTA ','CINCUENTA ','SESENTA ','SETENTA ','OCHENTA ','NOVENTA ','CIEN ')
        CENTENAS = ('CIENTO ','DOSCIENTOS ','TRESCIENTOS ','CUATROCIENTOS ',
                    'QUINIENTOS ','SEISCIENTOS ','SETECIENTOS ','OCHOCIENTOS ','NOVECIENTOS ')                    
        output = ''
        if(n == '100'):
            output = "CIEN "
        elif(n[0] != '0'):
            output = CENTENAS[int(n[0])-1]
        k = int(n[1:])
        if(k <= 20):
            output += UNIDADES[k]
        else:
            if((k > 30) & (n[2] != '0')):
                output += '%sY %s' % (DECENAS[int(n[1])-2], UNIDADES[int(n[2])])
            else:
                output += '%s%s' % (DECENAS[int(n[1])-2], UNIDADES[int(n[2])])
        return output

    def amount_to_text_pe(self,number_in, currency='SOLES'):
        #netsvc.Logger().notifyChannel("amount_to_text_pe",netsvc.LOG_INFO, "number_in: %s, currency: %s"%(number_in, currency))
        converted = ''                              
        if type(number_in) != 'str':
            number = str(round(number_in,2))   
        else:                       
            number = number_in        
        number_str=number                                      
        try:                                                   
            number_int, number_dec = number_str.split(".")       
        except ValueError:                                     
            number_int = number_str                              
            number_dec = ""                                      
        number_str = number_int.zfill(9)
        millones = number_str[:3]       
        miles = number_str[3:6]         
        cientos = number_str[6:]
        if(millones):
            if(millones == '001'):
                converted += 'UN MILLON '
            elif(int(millones) > 0):     
                converted += '%sMILLONES ' % self.__convertNumber(millones)
        if(miles):                                                    
            if(miles == '001'):                                       
                converted += 'MIL '                                   
            elif(int(miles) > 0):                                     
                converted += '%sMIL ' % self.__convertNumber(miles)        
        if(cientos):                                                  
            if(cientos == '001'):                                     
                converted += 'UN '                                    
            elif(int(cientos) > 0):                                   
                converted += '%s ' % self.__convertNumber(cientos)         
        if number_dec == "":
            number_dec = "00" 
        if (len(number_dec) < 2 ):
            number_dec+='0'         
        converted += 'y ' + number_dec + "/100 " + (currency or '')
        return converted

    def amount_to_text_bo(self,number_in, currency='BOLIVIANOS'):
        #netsvc.Logger().notifyChannel("amount_to_text_pe",netsvc.LOG_INFO, "number_in: %s, currency: %s"%(number_in, currency))
        converted = ''                              
        if type(number_in) != 'str':
            number = str(round(number_in,2))   
        else:                       
            number = number_in        
        number_str=number                                      
        try:                                                   
            number_int, number_dec = number_str.split(".")       
        except ValueError:                                     
            number_int = number_str                              
            number_dec = ""                                      
        number_str = number_int.zfill(9)
        millones = number_str[:3]       
        miles = number_str[3:6]         
        cientos = number_str[6:]
        if(millones):
            if(millones == '001'):
                converted += 'UN MILLON '
            elif(int(millones) > 0):     
                converted += '%sMILLONES ' % self.__convertNumber(millones)
        if(miles):                                                    
            if(miles == '001'):                                       
                converted += 'MIL '                                   
            elif(int(miles) > 0):                                     
                converted += '%sMIL ' % self.__convertNumber(miles)        
        if(cientos):                                                  
            if(cientos == '001'):                                     
                converted += 'UN '                                    
            elif(int(cientos) > 0):                                   
                converted += '%s ' % self.__convertNumber(cientos)         
        if number_dec == "":
            number_dec = "00" 
        if (len(number_dec) < 2 ):
            number_dec+='0'         
        converted += ' ' + number_dec + "/100 " + (currency or '')
        return converted

    def amount_to_text_ec(self,number_in, currency='DOLARES AMERICANOS'):
        #netsvc.Logger().notifyChannel("amount_to_text_pe",netsvc.LOG_INFO, "number_in: %s, currency: %s"%(number_in, currency))
        converted = ''                              
        if type(number_in) != 'str':
            number = str(round(number_in,2))   
        else:                       
            number = number_in        
        number_str=number                                      
        try:                                                   
            number_int, number_dec = number_str.split(".")       
        except ValueError:                                     
            number_int = number_str                              
            number_dec = ""                                      
        number_str = number_int.zfill(9)
        millones = number_str[:3]       
        miles = number_str[3:6]         
        cientos = number_str[6:]
        if(millones):
            if(millones == '001'):
                converted += 'UN MILLON '
            elif(int(millones) > 0):     
                converted += '%sMILLONES ' % self.__convertNumber(millones)
        if(miles):                                                    
            if(miles == '001'):                                       
                converted += 'MIL '                                   
            elif(int(miles) > 0):                                     
                converted += '%sMIL ' % self.__convertNumber(miles)        
        if(cientos):                                                  
            if(cientos == '001'):                                     
                converted += 'UN '                                    
            elif(int(cientos) > 0):                                   
                converted += '%s ' % self.__convertNumber(cientos)         
        if number_dec == "":
            number_dec = "00" 
        if (len(number_dec) < 2 ):
            number_dec+='0'         
        converted += 'y ' + number_dec + "/100 " + (currency or '')
        return converted

    def amount_to_text_ar(self,number_in, currency='PESOS ARGENTINOS'):
        #netsvc.Logger().notifyChannel("amount_to_text_pe",netsvc.LOG_INFO, "number_in: %s, currency: %s"%(number_in, currency))
        converted = ''                              
        if type(number_in) != 'str':
            number = str(round(number_in,2))   
        else:                       
            number = number_in        
        number_str=number                                      
        try:                                                   
            number_int, number_dec = number_str.split(".")       
        except ValueError:                                     
            number_int = number_str                              
            number_dec = ""                                      
        number_str = number_int.zfill(9)
        millones = number_str[:3]       
        miles = number_str[3:6]         
        cientos = number_str[6:]
        if(millones):
            if(millones == '001'):
                converted += 'UN MILLON '
            elif(int(millones) > 0):     
                converted += '%sMILLONES ' % self.__convertNumber(millones)
        if(miles):                                                    
            if(miles == '001'):                                       
                converted += 'MIL '                                   
            elif(int(miles) > 0):                                     
                converted += '%sMIL ' % self.__convertNumber(miles)        
        if(cientos):                                                  
            if(cientos == '001'):                                     
                converted += 'UN '                                    
            elif(int(cientos) > 0):                                   
                converted += '%s ' % self.__convertNumber(cientos)         
        if number_dec == "":
            number_dec = "00" 
        if (len(number_dec) < 2 ):
            number_dec+='0'         
        converted += 'y ' + number_dec + "/100 " + (currency or '')
        return converted

    def amount_to_text_cl(self,number_in, currency='PESOS CHILENOS'):
        #netsvc.Logger().notifyChannel("amount_to_text_pe",netsvc.LOG_INFO, "number_in: %s, currency: %s"%(number_in, currency))
        converted = ''                              
        if type(number_in) != 'str':
            number = str(round(number_in,2))   
        else:                       
            number = number_in        
        number_str=number                                      
        try:                                                   
            number_int, number_dec = number_str.split(".")       
        except ValueError:                                     
            number_int = number_str                              
            number_dec = ""                                      
        number_str = number_int.zfill(9)
        millones = number_str[:3]       
        miles = number_str[3:6]         
        cientos = number_str[6:]
        if(millones):
            if(millones == '001'):
                converted += 'UN MILLON '
            elif(int(millones) > 0):     
                converted += '%sMILLONES ' % self.__convertNumber(millones)
        if(miles):                                                    
            if(miles == '001'):                                       
                converted += 'MIL '                                   
            elif(int(miles) > 0):                                     
                converted += '%sMIL ' % self.__convertNumber(miles)        
        if(cientos):                                                  
            if(cientos == '001'):                                     
                converted += 'UN '                                    
            elif(int(cientos) > 0):                                   
                converted += '%s ' % self.__convertNumber(cientos)         
        if number_dec == "":
            number_dec = "00" 
        if (len(number_dec) < 2 ):
            number_dec+='0'         
        converted += 'y ' + number_dec + "/100 " + (currency or '')
        return converted


    def amount_to_text_py(self,number_in, currency='GUARANIES'):
        #netsvc.Logger().notifyChannel("amount_to_text_pe",netsvc.LOG_INFO, "number_in: %s, currency: %s"%(number_in, currency))
        converted = ''                              
        if type(number_in) != 'str':
            number = str(round(number_in,2))   
        else:                       
            number = number_in        
        number_str=number                                      
        try:                                                   
            number_int, number_dec = number_str.split(".")       
        except ValueError:                                     
            number_int = number_str                              
            number_dec = ""                                      
        number_str = number_int.zfill(9)
        millones = number_str[:3]       
        miles = number_str[3:6]         
        cientos = number_str[6:]
        if(millones):
            if(millones == '001'):
                converted += 'UN MILLON '
            elif(int(millones) > 0):     
                converted += '%sMILLONES ' % self.__convertNumber(millones)
        if(miles):                                                    
            if(miles == '001'):                                       
                converted += 'MIL '                                   
            elif(int(miles) > 0):                                     
                converted += '%sMIL ' % self.__convertNumber(miles)        
        if(cientos):                                                  
            if(cientos == '001'):                                     
                converted += 'UN '                                    
            elif(int(cientos) > 0):                                   
                converted += '%s ' % self.__convertNumber(cientos)         
        if number_dec == "":
            number_dec = "00" 
        if (len(number_dec) < 2 ):
            number_dec+='0'         
        converted += 'y ' + number_dec + "/100 " + (currency or '')
        return converted

    def amount_to_text_co(self,number_in, currency="PESOS"):
        #netsvc.Logger().notifyChannel("amount_to_text_pe",netsvc.LOG_INFO, "number_in: %s, currency: %s"%(number_in, currency))
        converted = ''
        if type(number_in) != 'str':
            number = str(round(number_in,0))
        else:
            number = number_in
        number_str=number
        try:
            number_int, number_dec = number_str.split(".")
        except ValueError:
            number_int = number_str
            number_dec = ""
        number_str = number_int.zfill(9)
        millones = number_str[:3]
        miles = number_str[3:6]
        cientos = number_str[6:]
        if(millones):
            if(millones == '001'):
                converted += 'UN MILLON '
            elif(int(millones) > 0):
                converted += '%sMILLONES ' % self.__convertNumber(millones)
        if(miles):
            if(miles == '001'):
                converted += 'MIL '
            elif(int(miles) > 0):
                converted += '%sMIL ' % self.__convertNumber(miles)
        if(cientos):
            if(cientos == '001'):
                converted += 'UN '
            elif(int(cientos) > 0):
                converted += '%s ' % self.__convertNumber(cientos)
        if number_dec == "":
            number_dec = "00"
        if (len(number_dec) < 2 ):
            number_dec+='0'
        converted += ' ' + currency
        return converted

#-------------------------------------------------------------
# Generic functions
#-------------------------------------------------------------
    _translate_funcs = {'co': 'self.amount_to_text_co', 'pe': 'self.amount_to_text_pe', 'es': 'self.amount_to_text_pe', 
                        'en': 'self.amount_to_text_en', 'py': 'self.amount_to_text_pe', 'bo': 'self.amount_to_text_bo',
                        'ar': 'self.amount_to_text_ar', 'cl': 'self.amount_to_text_cl', 'ec': 'self.amount_to_text_ec'}

    def add_amount_to_text_function(self,lang, func):
        self._translate_funcs[lang] = func

    def amount_to_text(self, nbr, lang='pe', currency=False):
        if not self._translate_funcs.has_key(lang):
            netsvc.Logger().notifyChannel("amount_to_text",netsvc.LOG_INFO, "WARNING: no translation function found for lang: '%s'" % (lang,))
            lang = 'en'
        if currency:
            exec("res = %s(abs(nbr), currency)"%(self._translate_funcs[lang]))
        else:
            exec("res = %s(abs(nbr))"%(self._translate_funcs[lang]))
        return res
    
    # part : day, month, year
    # format: text, number
    def date_part(self, date, part , format='number' ,lang='pe'):
        if isinstance(date,datetime.datetime):
            date = date.strftime('%Y-%m-%d')
        #netsvc.Logger().notifyChannel("date_part",netsvc.LOG_INFO, "date=%s, part=%s, format=%s, lang=%s" % (date,part,format,lang))
        MES = ('','ENERO ','FEBRERO ','MARZO ','ABRIL ','MAYO ','JUNIO ','JULIO ','AGOSTO ','SETIEMBRE ','OCTUBRE ','NOVIEMBRE ','DICIEMBRE ')
        res = ''
        if part=='day':
            if format=='number':
                res = date[8:10]
            else:
                res = self.__convertNumber(date[8:10])
        elif part=='month':
            if format=='number':
                res = date[5:7]
            else:
                res = MES[int(date[5:7])]
        elif part=='year':
            if format=='number':
                res = date[0:4]
            else:
                res = self.__convertNumber(date[0:4])
        else:
            res = date
        return res
    
    def date_to_text(self, date, format='number' ,lang='pe'):
        return self.date_part(date,'day',format='number') + ' de ' + self.date_part(date,'month',format='text') + ' del ' +  self.date_part(date,'year')
