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
from openerp.exceptions import except_orm, Warning, RedirectWarning


class DocumentCollection(models.TransientModel):
    _name = 'archives.document.collection'

    name = fields.Char('Collection Name')
    what_t2 = fields.Selection([('new', 'Create a New Collection'), ('add', 'Update an Existing Collection')],
                               'What do you want to do?', required=True,
                                help="""Use Create a New Collection to create a new collection with the selected documents.
                                    Use Update an Existing Collection to add the selected documents to a previous created
                                    collection.""")
    collection_id = fields.Many2one('archives.collection', 'Collection')
    parent_id = fields.Many2one('archives.collection', string="Copy Of")
    description = fields.Text('Description')
    document_ids = fields.One2many('archives.document.collection.item', 'wizard_id', 'Documents',
                                   default=lambda self: self._default_document_ids())

    @api.model
    def _default_document_ids(self):
        items = self.env['archives.document.collection.item']
        index = self._context.get('base_index', 0)

        for document in self.env['archives.document'].browse(self._context.get('active_ids')):
            index += 1
            items |= items.new({
                        'document_id': document,
                        'index': index,
                        })

        return items

    @api.one
    @api.onchange('collection_id')
    def _onchange_collection_id(self):
        items_in_collection = self.env['archives.document.collection.item']
        index = 0

        for document in self.env['archives.document'].search([('collection_id', '=', self.collection_id.id)], order='index asc'):
            index = document.index
            items_in_collection |= items_in_collection.new({
                                            'document_id': document,
                                            'index': index,
                                            })
        items_in_collection |= self.wich_context(base_index= index)._default_document_ids()

        self.document_ids = items_in_collection

    @api.multi
    def create_collection(self):
        pass

    @api.multi
    def action_document_collection(self):
        if self._context.get('active_model') == 'archives.document' and self.env['archivis.document'].browse(
                        self._context.get('active_ids')
                        ).filtered(lambda d: r.collection_id != False):
            raise Warning(_('Error!'), _(
                'The selected requisitions are already associated to a collection.'
                ))

        action = self.env.ref('archives.purchase_requisition_merge').read()[0]
        action['context'] = self._context.copy()

        return action


class DocumentCollectionItem(models.TransientModel):
    _name = "archives.document.collection.item"

    wizard_id = fields.Many2one('arvhives.document.collection', 'Document Collection', required=True,
                                    ondelete='cascade')
    index = fields.Integer('Document Index', required=True, default=1)
    document_id = fields.Many2one('archives.document', 'Document', required=True,
                                  domain="[('collection_id', '=', False)]")
    in_collection = fields.Boolean('In Collection', help="Already in Collection",
                              compute='_compute_in_collection')

    @api.multi
    @api.depends('document_id.collection_id')
    def _compute_in_collection(self):
        for record in self:
            record.in_collection = record.document_id.collection_id