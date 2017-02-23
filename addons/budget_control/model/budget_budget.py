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


class BudgetStruct(models.Model):
    _inherit = "budget.struct"

    @api.multi
    def _compute(self):
        company_id = self._context.get('company_id', self.env['res.company'].company_default_get('budget.budget').id)
        period_id = self._context.get('date',False) and self.env['budget.period'].find(dt=self._context['date']) or self.env['budget.period'].find()
        period_id = self._context.get('budget_period_id', period_id and period_id[0].id or 0)
        analytic_id = self._context.get('analytic_id', False)
        state = self._context.get('state', 'done')
        for struct in self:
            struct_ids = [struct.id] + [c.id for c in struct.full_child_ids]
            self._cr.execute(
                "SELECT sum(available), sum(committed), sum(provision), sum(paid) "
                "  FROM budget_move_line as bml join budget_move as bm on (bml.move_id=bm.id) "
                "WHERE bml.struct_id in %s AND bm.company_id = %s "
                "   AND bm.period_id = %s " +
                (analytic_id and "   AND bml.analytic_id = %s"%analytic_id or " ") +
                (state=='all' and " " or "   AND bm.state = 'done'"),
                (tuple(struct_ids), company_id, period_id))
            result = self._cr.fetchone()
            if result:
                struct.available = result[0]
                struct.committed = result[1]
                struct.provision = result[2]
                struct.paid = result[3]

    def get_formview_action(self, cr, uid, id, context=None):
        """ Return an action to open the document. This method is meant to be
            overridden in addons that want to give specific view ids for example.

            :param int id: id of the document to open
        """
        view_id = self.get_formview_id(cr, uid, id, context=context)
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'target': 'current',
            'res_id': id,
            'context': context,
        }

    available = fields.Float("Available", compute=_compute)
    committed = fields.Float("Committed", compute=_compute)
    provision = fields.Float("Provision", compute=_compute)
    paid = fields.Float("Paid", compute=_compute)
    verify_available = fields.Boolean("Verify Available",
                                      help="Restrict the overload of avaliable amounts. Use this option only for expense structs")
    verify_committed = fields.Boolean("Verify Committed",
                                      help="Restrict the overload of committed amounts. Use this option only for expense structs")
    verify_provision = fields.Boolean("Verify Provision",
                                      help="Restrict the overload of provisioned amounts. Use this option only for expense structs")
    verify_paid = fields.Boolean("Verify Paid",
                                      help="Restrict the overload of paid out amounts. Use this option only for expense structs")
