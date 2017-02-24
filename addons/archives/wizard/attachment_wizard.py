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
from openerp.exceptions import Warning


class AttachmentWizard(models.TransientModel):
    _name = "attachment.wizard"

    @api.model
    def _compute_domain_version_id(self):
        return [('document_id', '=', self._context.get('arch_document_id'))]

    def _compute_domain_attachment_id(self):
        return [('id', '=', 0)]

    def _domain_attachment_version_ids(self):
        version_last = self.env['archives.document.version'].search([('document_id', '=', self._context.get('arch_document_id'))],
                                                     limit=1, order='date desc')
        return [('archive_version_id', '=', version_last.id)]

    def _default_version_last(self):
        return self.env['archives.document.version'].search([('document_id','=',self._context.get('arch_document_id'))], limit=1, order='date desc')

    def _domain_attachment_by_document(self):
        version_ids = self.env['archives.document.version'].search([('document_id', '=', self._context.get('arch_document_id'))])
        list_viersion_id = []
        for v in version_ids:
            list_viersion_id.append(v.id)

        return [('archive_version_id', 'in', list_viersion_id)]

    def _domain_attachment_new(self):
        return [('id', '=', 0)]

    attachment_id = fields.Many2one('ir.attachment', 'Attachment', domain=_compute_domain_attachment_id)

    version_new = fields.Boolean('New version ?', default=False)

    version_id = fields.Many2one('archives.document.version','Document Version', domain=_compute_domain_version_id, default=lambda self: self.env['archives.document.version'].search([('document_id','=',self._context.get('arch_document_id'))], limit=1, order='date desc'))

    attachment_version_ids = fields.Many2many(
        'ir.attachment', 'attachment_last_version_rel', domain=_domain_attachment_by_document,
        string='Attachments Last Version')

    attachment_new_ids = fields.Many2many(
        'ir.attachment', 'attachment_new_version_rel',
        string='Attachments New', domain=_domain_attachment_new) #

    # attachment_new_ids = fields.One2many('attachment.new', 'attachment_wizard_id', string="Attachments New")

    @api.model
    def exists_template_in_list(self,att,list_t):
        val= False
        for l in list_t:
            if att.required:
                if att.attachment_template_id.id ==  l.attachment_template_id.id:
                    val = l
                    break
        return val

    @api.multi
    def save_version(self):

        # list_total = self.attachment_version_ids + self.attachment_new_ids
        # doc = self.env['archives.document'].browse(self._context.get('arch_document_id'))
        # for req in doc.attachment_required_ids:
        #     val = self.exists_template_in_list(req,list_total)
        #     if type(val) == bool:
        #         raise Warning(_('Warning!'), _(
        #             'For the selected version, %s is not defined and is mandatory') % (
        #                         req.name
        #                       ))
        #     else:
        #         req.datas = val.datas
        #         req.datas_fname = val.datas_fname


        versions_doc = self.env['archives.document.version'].search([('document_id', '=', self._context.get('arch_document_id'))])
        for v in versions_doc:
            v.state = 'disabled'

        self.version_id.state = 'enabled'

        self.version_id.document_id = self._context.get('arch_document_id')

        for att_v in self.attachment_version_ids:
            att = att_v.copy()
            name = att.name.split('(copia)')
            if len(name) == 2:
                att.name = name[0]
                self.version_id.attachment_ids +=att
            else:
                name = att.name.split('(copy)')
                if len(name) == 2:
                    att.name = name[0]
                    self.version_id.attachment_ids += att

        # for new_att in self.attachment_new_ids:
        #     att_vals = new_att.read()[0]
            # att_vals = {
            #             'name': new_att.name,
            #             'description': new_att.description,
            #             'url': new_att.url,
            #             'file_size': new_att.file_size,
            #             'company_id': new_att.company_id.id,
            #             'write_date': new_att.write_date,
            #             'type': new_att.type,
            #             'store_fname': new_att.store_fname,
            #             'user_id': new_att.user_id.id,
            #             'archive_version_id': self.version_id.id,
            #             'attachment_template_id': new_att.attachment_template_id.id,
            #             'mimetype': 'application / octet - stream'
            #
            #         }



            # user_id = att_vals.get('user_id')[0]
            # att_vals.update({'user_id': user_id})
            #
            # attachment_template_id = att_vals.get('attachment_template_id')[0]
            # att_vals.update({'attachment_template_id': attachment_template_id})
            #
            # company_id = att_vals.get('company_id')[0]
            # att_vals.update({'company_id': company_id})
            #
            # create_uid = att_vals.get('create_uid')[0]
            # att_vals.update({'create_uid': create_uid})
            #
            # write_uid = att_vals.get('write_uid')[0]
            # att_vals.update({'write_uid': write_uid})
            #
            #
            # att= self.env['ir.attachment'].create(att_vals)
            # self.version_id.attachment_ids +=att
        self.version_id.attachment_ids += self.attachment_new_ids


class AttachmentNewWizard(models.TransientModel):
    _name = "attachment.new"
    _inherit = "ir.attachment"

    # attachment_id = fields.Many2one('ir.attachment', 'Attachment', default= lambda self: self.env['ir.attachment'].create())
    #
    # name = fields.Char('Name', related='attachment_id.name')
    #
    # template_id = fields.Many2one('ir.attachment', 'Attachment Template', related='attachment_id.attachment_template_id')
    #
    # data = fields.Binary('File', related='attachment_id.datas')

    attachment_wizard_id = fields.Many2one('attachment.wizard', 'Attachment Wizard')



