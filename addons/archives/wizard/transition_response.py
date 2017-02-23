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
from lxml import etree

from openerp import api, fields, models, _
from openerp import SUPERUSER_ID
from openerp.exceptions import Warning, except_orm

from openerp.tools.safe_eval import safe_eval as eval


class TransitionResponse(models.TransientModel):
    _name = "archives.transition.response"

    params = fields.Text('Params')

    @api.model
    def create(self, vals):
        """ compress wizard params in to params field and store it. """
        return super(TransitionResponse, self).create({'params': str(vals)})

    @api.multi
    def write(self, vals):
        """ compress wizard params in to params field and store it. """
        fields_2read = []
        if self._context.get('wzd_params'):
            for field_def in self._context.get('wzd_params', []):
                fields_2read.append(field_def['name'])

        for record in self:
            params_values = record.read(fields=fields_2read, load='_direct')[0] #{field_2read: record[field_2read] for field_2read in fields_2read}
            params_values.update(vals)
            super(TransitionResponse, record).write({'params': str(params_values)})

        return True

    @api.multi
    def read(self, fields=None, load='_classic_read'):
        """ un compress wizard params from params field and return its. """
        res = []

        for vals in super(TransitionResponse, self).read(fields=['params'], load=load):
            res2 = eval(vals['params'])
            res2['id'] = vals['id']
            res.append(res2)

        return res

    @api.model
    def fields_get(self, allfields=None, write_access=True, attributes=None):
        if self._context.get('wzd_params'):
            for wzd_param in self._context.get('wzd_params', []):
                field_def = wzd_param.copy()
                field_name = field_def.pop('name')
                field_type = field_def.pop('type')
                self._add_field(field_name, fields.Field.by_type[field_type](**field_def))
            self._setup_fields()

        res = super(TransitionResponse, self).fields_get(allfields=allfields, write_access=write_access,
                                                         attributes=attributes)
        return res

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(TransitionResponse, self).fields_view_get(view_id=view_id, view_type=view_type,
                                                              toolbar=toolbar, submenu=submenu)
        if view_type == 'form' and self._context.get('wzd_params'):
            field_defs = self._context.get('wzd_params', [])
            dom = etree.XML(res['arch'])
            for node in dom.xpath("//div[@name='wzd_params']"):
                xml_doc = self.env.ref('archives.transition_response_params').render(
                    {'response_field_defs': field_defs}
                ).strip()
                # xml_doc = '\n'.join(['<?xml version="1.0"?>', xml_doc])
                if xml_doc:
                    dom_fragment = etree.XML(xml_doc)
                    ref_node = node.getparent()
                    ref_node.remove(node)
                    ref_node.append(dom_fragment)

                    arch, fields = self.env['ir.ui.view'].postprocess_and_fields(self._name, dom, view_id)
                    res['fields'] = fields
                    res['arch'] = arch

                    # res['arch'] = etree.tostring(dom)

        return res

    @api.multi
    def action_response(self):
        Documents = self.env['archives.document']
        document_id = self._context.get('document_id')
        src_step_id = self._context.get('src_step_id')
        dst_step_id = self._context.get('dst_step_id')

        fields_2read = []
        if self._context.get('wzd_params'):
            for field_def in self._context.get('wzd_params', []):
                fields_2read.append(field_def['name'])

        for record in self:
            params_values = {field_2read: record[field_2read] for field_2read in fields_2read}
            res = Documents.with_context(
                            arch_tx_act_send=True
                            )._action_next_step(document_id, src_step_id, dst_step_id, **params_values)
            return res
