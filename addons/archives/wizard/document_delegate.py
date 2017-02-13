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
from openerp.tools import float_compare
import openerp.addons.decimal_precision as dp


class DocumentDelegate(models.TransientModel):
    _name = "archives.document.delegate"
    _description = "Escalate or Delegate Document Wizard"

    @api.model
    def _compute_user_id_domain(self):
        """ filter user by process and department ."""
        document =  self.env['archives.document'].browse(self._context.get('active_id'))
        employee = self.env.user.employee_ids[:1]

        candidates = self.env['hr.employee']

        if self._context.get('arch_behavior', 'escalate') == 'escalate':
            pass
        else:
            # first retrieve possible users of the same department
            candidates |= employee.department_id.member_ids.filtered(lambda e: e != employee.department_id.manager_id and
                                                                               e != employee.parent_id and
                                                                               e != employee.coach_id and
                                                                               e != employee)
            # sort the users according to process load_balancd policy
            candidates = self.env['archives.process.step'].sort_candidates(candidates, document.process_step_id)

            # later retrieve the manager of the subordinated departments
            candidates |= employee.department_id.mapped('child_ids.manager_id')

        return [('id', 'in', candidates.mapped('user_id').ids)]


    user_id = fields.Many2one('res.users', 'User to Delegate', required=True, auto_join=True,
                              domain=_compute_user_id_domain,
                              context="{'show_employee_job': True}")

    @api.multi
    def _compute_user_id(self):
        document =  self.env['archives.document'].browse(self._context.get('active_id'))
        employee = self.env.user.employee_ids[:1]

        candidates = self.env['res.users']

        if self._context.get('behavior', 'escalate') == 'escalate':
            pass
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
        for record in self:
            pass


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