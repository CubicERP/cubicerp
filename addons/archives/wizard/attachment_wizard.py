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
    def _compute_domain_version_id(self):
        return [('document_id', '=', self._context.get('arch_document_id'))]

    def _compute_domain_attachment_id(self):
        return [('id', '=', 0)]


    attachment_id = fields.Many2one('ir.attachment', 'Attachment', domain=_compute_domain_attachment_id)

    version_new = fields.Boolean('New version ?', default=False)

    version_id = fields.Many2one('archives.document.version','Document Version', domain=_compute_domain_version_id, default=lambda self: self.env['archives.document.version'].search([('document_id','=',self._context.get('arch_document_id'))], limit=1, order='date desc'))

    @api.model
    def _default_version_last(self):
        return self.env['archives.document.version'].search([('document_id','=',self._context.get('arch_document_id'))], limit=1, order='date desc')


    @api.multi
    def save_version(self):

        if not self.version_new and self.version_id.id:
            self.version_id.attachment_ids += self.attachment_id
        else:
            number = 1
            if self.version_id.id:
                number = self.version_id.version_number
                number += 1

            version_vals = {
                'version_number': number,
                'name': 'Version_'+str(number),
                'date': datetime.datetime.now(),
                'document_id': self._context.get('arch_document_id')
            }

            vers= self.env['archives.document.version'].create(version_vals)
            vers.attachment_ids += self.attachment_id
            doc = self.env['archives.document'].browse(self._context.get('arch_document_id'))
            doc.version_ids += vers





