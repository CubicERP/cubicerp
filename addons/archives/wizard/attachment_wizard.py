# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import api, fields, models, _
import datetime


class AttachmentWizard(models.TransientModel):
    _name = "attachment.wizard"

    @api.model
    def _compute_version_id_domain(self):
        return [('document_id', '=', self._context.get('arch_document_id'))]

    document_id = fields.Many2one('archives.document','Document',default=lambda self: self._context.get('active_id'))

    user_id = fields.Many2one('res.users','Owner', default=lambda self: self._uid)

    name = fields.Char('Attachment Name', required=True)

    type_data = fields.Selection([('url', 'URL'), ('binary', 'Binary'), ],'Type', help="Binary File or URL", required=True, default='binary')

    url = fields.Char('Url', size=1024)

    data = fields.Binary(string='File Content')

    version_id = fields.Many2one('archives.document.version','Document Version', domain=_compute_version_id_domain, default=lambda self: self.env['archives.document.version'].search([('document_id','=',self._context.get('arch_document_id'))], limit=1, order='date desc'))

    description = fields.Text('Description')

    version_new = fields.Boolean('New version ?', default=False)

    version_number = fields.Integer('Version Number')

    @api.model
    def _default_version_last(self):
        return self.env['archives.document.version'].search([('document_id','=',self._context.get('arch_document_id'))], limit=1, order='date desc')


    @api.multi
    def save_version(self):

        attch_vals = {
            'name': self.name,
            'type': self.type_data,
            'datas': self.data,
            'url': self.url,
            'user_id': self.user_id.id,
            'description': self.description,
        }
        attch = self.env['ir.attachment'].create(attch_vals)

        if not self.version_new and self.version_id.id:
            self.version_id.attachment_ids += attch
        else:
            number = 1
            if self.version_id.id:
                number = self.version_id.version_number
                number += 1

            version_vals = {
                'version_number': number,
                'name': 'Version_'+str(number),
                'date': datetime.datetime.now(),
                'document_id': self.document_id.id,
            }

            vers= self.env['archives.document.version'].create(version_vals)
            vers.attachment_ids += attch
            self.document_id.version_ids += vers






