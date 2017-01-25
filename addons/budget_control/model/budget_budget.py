# -*- coding: utf-8 -*-
##############################################################################
#
#    Cubic ERP, Enterprise Management Software
#    Copyright (C) 2017 Cubic ERP SAC (<http://cubicerp.com>).
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
        period_id = self.env['budget.period'].find()
        period_id = self._context.get('budget_period_id', period_id and period_id[0].id or 0)
        state = self._context.get('state', 'done')
        for struct in self:
            struct_ids = [struct.id] + [c.id for c in struct.full_child_ids]
            self._cr.execute(
                "SELECT sum(available), sum(committed), sum(provision), sum(paid) "
                "  FROM budget_move_line as bml join budget_move as bm on (bml.move_id=bm.id) "
                "WHERE bml.struct_id in %s AND bm.company_id = %s "
                "   AND bm.period_id = %s " +
                (state=='all' and " " or "   AND bm.state = 'done'"),
                (tuple(struct_ids), company_id, period_id))
            result = self._cr.fetchone()
            if result:
                struct.available = result[0]
                struct.committed = result[1]
                struct.provision = result[2]
                struct.paid = result[3]

    available = fields.Float("Available", compute=_compute)
    committed = fields.Float("Committed", compute=_compute)
    provision = fields.Float("Provision", compute=_compute)
    paid = fields.Float("Paid", compute=_compute)
