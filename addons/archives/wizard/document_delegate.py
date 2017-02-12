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

import itertools
from lxml import etree

from openerp import api, fields, models, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.tools import float_compare
import openerp.addons.decimal_precision as dp


class DocumentDelegate(models.TransientModel):
    _name = "archives.document.delegate"
    _description = "Escalate or Delegate Document Wizard"

    user_id = fields.Many2one('res.users', 'User to Delegate', required=True, auto_join=True,
                              compute="_compute_user_id", store=True, context="{'show_employee_job': True}")

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
            # later retrieve the manager of the subordinated departments
            candidates |= employee.department.mapped('child_ids.manager_id.user_id')


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