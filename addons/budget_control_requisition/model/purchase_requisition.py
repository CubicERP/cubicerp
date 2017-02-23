# -*- coding: utf-8 -*-
##############################################################################
#
#    Cubic ERP, Enterprise and Government Management Software
#    Copyright (C) 2017 Cubic ERP S.A.C. (<http://cubicerp.com>).
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

from openerp import models, fields, api, _


class PurchaseRequisition(models.Model):
    _inherit = "purchase.requisition"


    @api.multi
    @api.depends('struct_id', 'account_analytic_id', 'ordering_date')
    def _compute_available(self):
        for requisition in self:
            if requisition.struct_id:
                ctx = self._context.copy()
                if requisition.account_analytic_id:
                    ctx['analytic_id'] = requisition.account_analytic_id.id
                if requisition.ordering_date:
                    ctx['ordering_date'] = requisition.ordering_date
                requisition.available = requisition.struct_id.with_context(ctx).available

    struct_id = fields.Many2one('budget.struct', string='Budget Struct', states={'done': [('readonly', True)],
                                                                                 'cancel': [('readonly', True)]})
    available = fields.Float(string="Available", compute=_compute_available, store=True)

