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
import time

class l10n_pe_4ta_suspension(osv.Model):
    _name = "l10n_pe_4ta.suspension"
    _columns = {
            'partner_id': fields.many2one('res.partner', string="Partner", required=True),
            'property_fiscalyear_id': fields.property(type='many2one' ,
                                                      relation='account.fiscalyear',
                                                      string="fiscal Year",
                                                      required=True),
            'name': fields.char('Order Number',16),
            'application_result': fields.selection([('valid','Valid'),
                                                    ('invalid','Invalid')], string='Application Result', required=True),
            'application_date': fields.date('Application Date'),
            'application_end': fields.date('Application End'),
        }
    _defaults = {
            'application_result': 'valid',
            'application_date': lambda *a: time.strftime('%Y-%m-%d'),
            'property_fiscalyear_id': lambda s,cr,u,c: s.pool.get('account.fiscalyear').find(cr,u,context=c),
            'application_end': lambda s,cr,u,c: s.pool.get('account.fiscalyear').browse(cr,u,s.pool.get('account.fiscalyear').find(cr,u,context=c),context=c).date_stop,
        }
    _sql_constraints = [('partner_name_uniq','unique(partner_id,name)', 
                         'Partner and order number must be unique!')]
    
    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        if context is None: context = {}
        return [(r['id'], (str("[%s%s] %s"%(r.property_fiscalyear_id.name,r.name and (' - '+r.name) or '',r.partner_id.name)) or '')) for r in self.browse(cr, uid, ids, context=context)]

    
