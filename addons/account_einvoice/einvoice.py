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
from openerp.tools.translate import _
from StringIO import StringIO
import zipfile

class einvoice_server(osv.Model):
    _name = "einvoice.server"
    
    _columns = {
            'name': fields.char('Name', 64, required=True, readonly=True, states={'draft':[('readonly',False)],}),
            'url': fields.char('URL', 1024, required=True, readonly=True, states={'draft':[('readonly',False)],}),
            'user': fields.char('User', 64, readonly=True, states={'draft':[('readonly',False)],}),
            'password': fields.char('Password', 64, readonly=True, states={'draft':[('readonly',False)],}),
            'notes': fields.text('Notes'),
            'state': fields.selection([('draft','Draft'),
                                       ('ready','Ready')], string='State', readonly=True),
        }
    _defaults = {
            'state': 'draft',
            'name': '/',
        }
    
    def action_draft(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'draft'}, context=context)
    
    def action_ready(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'ready'}, context=context)
    
    
class einvoice_batch(osv.AbstractModel):
    _name = "einvoice.batch"
    _inherit = ['mail.thread','ir.needaction_mixin']
    
    _columns = {
            'name': fields.char('Name', 64, required=True, readonly=True, states={'draft':[('readonly',False)],}),
            'company_id': fields.many2one('res.company', string='Company', required=True, readonly=True, states={'draft':[('readonly',False)],}),
            'state': fields.selection([('draft','Draft'),
                                       ('ready','Ready'),
                                       ('request','Requested'),
                                       ('to_fix','To Fix'),
                                       ('done','Done'),
                                       ('cancel','Cancel')], string='State', readonly=True),
        }
    _defaults = {
            'state': 'draft',
            'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'l10n_pe.ple', context=c),
        }
    
    def unlink(self, cr, uid, ids, context=None):
        for batch in self.browse(cr, uid, ids, context=context):
            if batch.state <> 'draft':
                raise osv.except_osv (_('Unlink Error'),
                       _('The batch %s (id:%s) must be in draft status to be deleted !')%(batch.name,batch.id))
        return self.unlink(cr, uid, ids, context=context)
    
    def action_draft(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'draft'}, context=context)

    def action_ready(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'ready'}, context=context)
        
    def action_request(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'request'}, context=context)
    
    def action_response(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'to_fix'}, context=context)
    
    def action_done(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'done'}, context=context)
    
    def action_cancel(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'cancel'}, context=context)
    
class einvoice_message(osv.AbstractModel):
    _name = "einvoice.message"
    
    _columns = {
            'date': fields.datetime('Date', readonly=True),
            'date_end': fields.datetime('Date', readonly=True, states={'draft':[('readonly',False)],}),
            'message': fields.text('Message', readonly=True, states={'draft':[('readonly',False)],}),
            'signature': fields.text('Signature', readonly=True, states={'draft':[('readonly',False)],}),
            'state': fields.selection([('draft','Draft'),
                                       ('send','Sended'),
                                       ('receive','Received'),
                                       ('cancel','Cancel')], string='State', readonly=True),
        }
    
    _defaults = {
            'state': 'draft',
            'date': fields.datetime.now,
        }
    
    _order = 'date desc'
    
    
    def action_draft(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'draft'}, context=context)
    
    def action_send(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'send'}, context=context)
    
    def action_receive(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'receive'}, context=context)
    
    def action_cancel(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'cancel'}, context=context)
    
    def get_response(self, cr, uid, zip_file, name, contex=None):
        zf=zipfile.ZipFile(StringIO(zip_file.decode('base64')))
        return zf.open(name).read()