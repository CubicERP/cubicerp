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

from openerp.osv import osv, fields, expression
from openerp.tools.translate import _
import time

class base_table(osv.osv):

    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        reads = self.read(cr, uid, ids, ['name','code','description'], context=context)
        res = []
        for record in reads:
            name = "%s%s%s"%(record['name'], record['description'] and ' - ' or '', record['description'] or '') 
            if record['code']:
                name = '[%s] %s'%(record['code'],name)
            res.append((record['id'], name))
        return res

    def name_search(self, cr, user, name, args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        args = args[:]
        ids = []
        if name:
            ids = self.search(cr, user, [('code', '=like', name+"%")]+args, limit=limit)
            if not ids:
                ids = self.search(cr, user, [('name', operator, name)]+ args, limit=limit)
            if not ids and len(name.split()) >= 2:
                #Separating code and name of account for searching
                operand1,operand2 = name.split(': ',1) #name can contain spaces e.g. OpenERP S.A.
                ids = self.search(cr, user, [('code', operator, operand1), ('name', operator, operand2)]+ args, limit=limit)
        else:
            ids = self.search(cr, user, args, context=context, limit=limit)
        return self.name_get(cr, user, ids, context=context)

    def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.name_get(cr, uid, ids, context=context)
        return dict(res)

    _name = 'base.table'
    _description = 'Base Table of Tables'
    _columns = {
            'company_id' : fields.many2one('res.company','Company', select=True),
            'country_id' : fields.many2one('res.country','Company', select=True),
            'code' : fields.char('Code', size=32, select=True, required=True),
            'name': fields.char('Name', size=2048, required=True, translate=True, select=True),
            'complete_name': fields.function(_name_get_fnc, method=True, type="char", string='Name'),
            'description': fields.text('Description'),
            'parent_id': fields.many2one('base.table','Parent Table', select=True, domain=[('type','=','view')]),
            'child_ids': fields.one2many('base.table', 'parent_id', string='Child Tables'),
            'type': fields.selection([('view','View'), ('normal','Normal')], 'Table Type'),
            'active': fields. boolean('Active'),
            'element_ids': fields.one2many('base.element','table_id',string="Elements"),            
        }
    _defaults = {
            'active' : True,
            'type' : 'normal',
        }
    _sql_constraints = [('code_unique','unique(company_id,code)',_('The code must be unique!'))]

    _order = "code"
    def _check_recursion(self, cr, uid, ids, context=None):
        level = 100
        while len(ids):
            cr.execute('select distinct parent_id from base_table where id IN %s',(tuple(ids),))
            ids = filter(None, map(lambda x:x[0], cr.fetchall()))
            if not level:
                return False
            level -= 1
        return True

    _constraints = [
        (_check_recursion, _('Error ! You can not create recursive table of tables.'), ['parent_id'])
    ]
    def child_get(self, cr, uid, ids):
        return [ids]
    

class base_element(osv.osv):
    _name = 'base.element'
    _description = 'Elements in table of tables'
    _columns = {
            'table_id': fields.many2one('base.table','Base Table',select=True),
            'code': fields.char('Element Code', size=32, select=True),
            'name': fields.char('Element Name', size=64, select=True, required=True),
            'description': fields.text('Element Description'),
            'parent_id': fields.many2one('base.element',string="Element Parent"),
            'element_char': fields.char('Element String', size=1024),
            'element_float': fields.float('Element Float'),
            'element_percent': fields.float('Element Percent', help="Insert the number without the percent symbol. Examples: for 100% is 100, for 3.75% is 3.75"),
            'element_date': fields.date('Element Date'),
            'start_date': fields.date('Start Date'),
            'end_date': fields.date('End Date'),
            'interval_init_infinity': fields.boolean('Infinity Negative'),
            'interval_init_close': fields.boolean('Value >= Interval Initial'),
            'interval_init': fields.float('Inverval Initial'),
            'interval_end_infinity': fields.boolean('Infinity Positive'),
            'interval_end_close': fields.boolean('Value <= Interval End'),
            'interval_end': fields.float('Inverval End'),
            'sequence': fields.integer('Sequence'),
            'active': fields.boolean('Active'),
        }
    _defaults = {
            'active' : True,
            'sequence': 5,
            'interval_init_infinity': True,
            'interval_end_infinity': True,
        }
    _sql_constraints = [('table_name_unique','unique(table_id,name,start_date,interval_init)',_('The element code must be unique for this table!'))]
    
    def name_get(self, cr, user, ids, context=None):
        if not ids:
            return []
        if isinstance(ids, (int, long)):
            ids = [ids]
        result = self.browse(cr, user, ids, context=context)
        res = []
        for rs in result:
            name = "%s - %s" % (rs.name, rs.description)
            res += [(rs.id, name)]
        return res
    
    def name_search(self, cr, user, name, args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        if operator in expression.NEGATIVE_TERM_OPERATORS:
            domain = [('name', operator, name), ('description', operator, name)]
        else:
            domain = ['|', ('name', operator, name), ('description', operator, name)]
        ids = self.search(cr, user, expression.AND([domain, args]), limit=limit, context=context)
        return self.name_get(cr, user, ids, context=context)
    
    def get_element(self, cr, uid, table_code, element_code, field, date=None, interval_value=None, company_id=False, context={}):
        sql = "select e.%s from base_element e,base_table t where e.table_id=t.id and t.active=True and e.active=True and t.type<>'view' and t.code='%s' and e.name='%s'"%(field,table_code,element_code)
        sql += self.get_where(cr,uid, date=date,interval_value=interval_value,context=context)
        cr.execute(sql)
        return cr.fetchone()

    def get_elements(self, cr, uid, table_code, field, date=None, interval_value=None, company_id=False, context={}):
        sql = "select e.%s from base_element e,base_table t where e.table_id=t.id and t.type<>'view' and t.active=True and e.active=True and t.code='%s'"%(field,table_code)
        sql += self.get_where(cr,uid, date=date,interval_value=interval_value,context=context)
        cr.execute(sql)
        return [x[0] for x in cr.fetchall()]
    
    def get_as_selection(self, cr, uid, table_code, date=time.strftime('%Y-%m-%d'), interval_value=None, company_id=False, context=None):
        sql = "select e.name, e.element_char from base_element e,base_table t where e.table_id=t.id and t.type<>'view' and t.active=True and e.active=True and t.code='%s'"%(table_code)
        sql += self.get_where(cr,uid, date=date,interval_value=interval_value,context=context)
        cr.execute(sql)
        return [(x[0],x[1]) for x in cr.fetchall()]
    
    def get_selection(self, cr, uid, table_code, date=time.strftime('%Y-%m-%d'), interval_value=None, company_id=False, context=None):
        sql = "select e.name, e.description from base_element e,base_table t where e.table_id=t.id and t.type<>'view' and t.active=True and e.active=True and t.code='%s'"%(table_code)
        sql += self.get_where(cr,uid, date=date,interval_value=interval_value,context=context) 
        cr.execute(sql)
        return [(x[0],x[1]) for x in cr.fetchall()]
    
    def get_where(self, cr, uid, date=None, interval_value=None, company_id=False, context=None):
        res = ''
        if date: res += " and coalesce(start_date,'%s')<='%s' and coalesce(end_date,'%s')>='%s'"%(date,date,date,date)
        if interval_value is not None:
            res += " and case when interval_init_infinity then %s else interval_init + (case when interval_init_close then 0 else 0.00000000000001 end) end  <= %s"%(interval_value,interval_value)
            res += " and case when interval_end_infinity then %s else interval_end - (case when interval_end_close then 0 else 0.00000000000001 end) end >= %s"%(interval_value,interval_value)
        if company_id:
            res += " and (company_id is null or company_id=%s)"%company_id
        return res
    
    def browse_elements(self, cr, uid, table_code, date=time.strftime('%Y-%m-%d'), interval_value=None, company_id=False, context={}):
        return self.browse(cr,uid,self.get_elements(cr,uid,table_code,'id',date=date,interval_value=interval_value,company_id=company_id,context=context),context=context)

    def element_exists(self, cr, uid, table_code, element_code, date=time.strftime('%Y-%m-%d'), interval_value=None, company_id=False, context={}):
        return bool(self.get_element(cr,uid,table_code,element_code,'id',date=date,interval_value=interval_value,company_id=company_id,context=context))
    
    def get_element_percent(self, cr, uid, table_code, element_code, date=time.strftime('%Y-%m-%d'), interval_value=None, company_id=False, context={}):
        val = self.get_element(cr,uid,table_code,element_code,'element_percent',date=date,interval_value=interval_value,company_id=company_id,context=context)
        return val and val[0] or 0.0
        
    def get_percent(self, cr, uid, table_code, element_name, date=time.strftime('%Y-%m-%d'), interval_value=None, company_id=False, context={}):
        val = self.get_element(cr,uid,table_code,element_name,'element_percent',date=date,interval_value=interval_value,company_id=company_id,context=context)
        return val and val[0]/100.0 or 0.0
        
    def get_element_float(self, cr, uid, table_code, element_code, date=time.strftime('%Y-%m-%d'), interval_value=None, company_id=False, context={}):
        val = self.get_element(cr,uid,table_code,element_code,'element_float',date=date,interval_value=interval_value,company_id=company_id,context=context)
        return val and val[0] or 0.0

    def get_float(self, cr, uid, table_code, element_name, date=time.strftime('%Y-%m-%d'), interval_value=None, company_id=False, context={}):
        val = self.get_element(cr,uid,table_code,element_name,'element_float',date=date,interval_value=interval_value,company_id=company_id,context=context)
        return val and val[0] or 0.0
    
    def get_element_char(self, cr, uid, table_code, element_code, date=time.strftime('%Y-%m-%d'), interval_value=None, company_id=False, context={}):
        val = self.get_element(cr,uid,table_code,element_code,'element_char',date=date,interval_value=interval_value,company_id=company_id,context=context)
        return val and val[0] or ''
    
    def get_char(self, cr, uid, table_code, element_name, date=time.strftime('%Y-%m-%d'), interval_value=None, company_id=False, context={}):
        val = self.get_element(cr,uid,table_code,element_name,'element_char',date=date,interval_value=interval_value,company_id=company_id,context=context)
        return val and val[0] or ''
