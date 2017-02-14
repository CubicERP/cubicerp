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
from lxml import etree

from openerp import api, fields, models, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.tools import float_compare
import openerp.addons.decimal_precision as dp


class DocumentDelegate(models.TransientModel):
    _name = "archives.document.delegate"
    _description = "Escalate or Delegate Document Wizard"

    @api.model
    def _compute_user_id_domain(self):
        """ filter user by process and department ."""
        # document =  self.env['archives.document'].browse(self._context.get('active_id'))
        employee = self.env.user.employee_ids[:1]

        candidates = self.env['hr.employee']

        if self._context.get('arch_behavior', 'escalate') == 'escalate':
            candidates |= employee.department_id.search([
                                    ('parent_left', '<=', employee.department_id.parent_left),
                                    ('parent_right', '>=', employee.department_id.parent_right),
                                    ]).mapped('manager_id')
        else:
            # first retrieve possible users of the same department
            candidates |= employee.department_id.member_ids.filtered(lambda e: e != employee.department_id.manager_id and
                                                                               e != employee.parent_id and
                                                                               e != employee.coach_id and
                                                                               e != employee)
            # # sort the users according to process load_balancd policy
            # candidates = self.env['archives.process.step'].sort_candidates(candidates, document.process_step_id)

            # later retrieve the manager of the subordinated departments
            candidates |= employee.department_id.mapped('child_ids.manager_id')

        return [('id', 'in', candidates.mapped('user_id').ids)]


    document_id = fields.Many2one('archives.document', 'Document', readonly=True, auto_join=True,
                                  default=lambda self: self._context.get('active_id'))
    user_id = fields.Many2one('res.users', 'User to Delegate', required=True, auto_join=True,
                              domain=_compute_user_id_domain)
    move_type_id = fields.Many2one('archives.document.move.type', 'Move Type', required=True, auto_join=True)

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        res = super(DocumentDelegate, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        doc = etree.XML(res['arch'])

        if self._context.get('arch_behavior', 'delegate') == 'escalate':
            for node in doc.xpath("//form | //button | //field[@name='user_id']"):
                string = node.get('string')
                if node.tag == 'field':
                    string = 'User to Delegate'
                string = string.replace('Delegate', 'Escalate')
                node.set('string', string)

        res['arch'] = etree.tostring(doc)

        return res


    @api.multi
    def _compute_user_id(self):
        document =  self.env['archives.document'].browse(self._context.get('active_id'))
        employee = self.env.user.employee_ids[:1]

        candidates = self.env['res.users']

        if self._context.get('behavior', 'escalate') == 'escalate':
            candidates |= employee.departement_id.search([
                                        ('parent_left', '<=', employee.department_id.parentt_left),
                                        ('parent_right', '>=', employee.department_id.prent_right),
                                        ]).mapped('manager_id')
        else:
            # first retrieve possible users of the same department
            candidates |= employee.department_id.member_ids.filtered(lambda e: e != employee.department_id.manager_id or
                                                                               e != employee.parent_id or
                                                                               e != employee.coach_id or
                                                                               e != employee).mapped('user_id')
            # sort the users according to process load_balancd policy
            candidates = document.process_step_id.sort_candidates(candidates)

            # later retrieve the manager of the subordinated departments
            candidates |= employee.department.mapped('child_ids.manager_id.user_id')

        self.user_id = candidates

    @api.multi
    def delegate(self):
        """ create a document move

        Create a document move movement $ also update the previous one date_end field
        """
        DocumentMove = self.env['archives.document.move']

        for record in self:
            # create a movement for the document
            document_last_move = record.document_id.move_ids[:1]

            source_department_id = document_last_move.dest_department_id
            if not source_department_id:
                source_department_id = record.document_id.process_step_id.department_id

            dest_department_id = record.user_id.employee_ids[:1].department_id
            if not dest_department_id:
                dest_department_id = record.document_id.process_step_id.department_id

            source_user_id = document_last_move.dest_user_id
            if not source_user_id:
                if record.document_id.process_step_id.department_id:
                    source_user_id = record.document_id.process_step_id.department_id.manager_id
                else:
                    source_user_id = self.env.user

            document_curr_move = DocumentMove.create({
                                    'document_id': record.document_id.id,
                                    'document_step_id': record.document_id.step_ids[:1].id,
                                    'type': record.move_type_id.id,
                                    'date_start': fields.Datetime.now(),
                                    'source_department_id': source_department_id and source_department_id.id or False,
                                    'dest_department_id': dest_department_id and dest_department_id.id or False,
                                    'source_user_id': source_user_id and source_user_id.id or False,
                                    'dest_user_id': record.user_id.id,
                                    })
            # update the date_end of the previos las movement
            document_last_move.write({'date_end': document_curr_move.date_start})


class DocumentDelegateUser(models.Model):
    _inherit = 'res.users'

    @api.multi
    def name_get(self):
        result = super(DocumentDelegateUser, self.with_context(
                                                    show_address_only=False,
                                                    show_address=False,
                                                    show_email=False
                                                    )).name_get()

        # append the first employee's job
        if self._context.get('show_employee_job', False):
            return map(
                lambda t: (t[0], '%s, %s' % (t[1], self.browse(t[0]).employee_ids[:1].job_id.name or '')),
                result
                )

        return result


class HrDepartment(models.Model):
    """ Extended for optimal hierarchy search"""
    _inherit = "hr.department"

    _parent_store = True
    _order = 'parent_left'


    parent_left = fields.Integer('Parent Left')
    parent_right = fields.Integer("Parent Right")

