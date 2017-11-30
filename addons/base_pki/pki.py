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

class pki_certificate(osv.Model):
    _name="pki.certificate"
    
    _columns = {
            'name': fields.char('Name', 64, required=True, readonly=True, states={'draft':[('readonly',False)],}),
            'key': fields.text('Private Key', readonly=True, states={'draft':[('readonly',False)],}),
            'csr': fields.text('Certificate Request', readonly=True, states={'draft':[('readonly',False)],}),
            'crt': fields.text('Certificate .crt', readonly=True, states={'draft':[('readonly',False)],'request':[('readonly',False)],}),
            'cer': fields.text('Certificate .cer', readonly=True, states={'draft':[('readonly',False)],'request':[('readonly',False)],}),
            'pem': fields.text('Certificate .pem', readonly=True, states={'draft':[('readonly',False)],'request':[('readonly',False)],}),
            'der': fields.binary('Certificate .der', readonly=True, states={'draft':[('readonly',False)],'request':[('readonly',False)],}),
            'start_date': fields.date('Start Date', required=True, readonly=True, states={'draft':[('readonly',False)],'request':[('readonly',False)],}),
            'stop_date': fields.date('Stop Date', required=True, readonly=True, states={'draft':[('readonly',False)],'request':[('readonly',False)],}),
            'parent_id': fields.many2one('pki.certificate', string='Parent Certificate', readonly=True, states={'draft':[('readonly',False)],}),
            'state': fields.selection([('draft','Draft'),
                                       ('request','Requested'),
                                       ('done','Done'),
                                       ('cancel','Cancel')], string='State', readonly=True),
        }
    _defaults = {
            'state': 'draft',
        }
    
    def action_draft(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'draft'}, context=context)
    
    def action_request(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'request'}, context=context)
    
    def action_done(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'done'}, context=context)
    
    def action_cancel(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'cancel'}, context=context)