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

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp

class MrpProductionSchedule(models.TransientModel):
    _name = 'mrp.workorder.record.production'

    workorder_id = fields.Many2one("mrp.workorder", required=True)
    user_id = fields.Many2one("res.users", default=lambda s: s.env.user.id, required=True)
    qty_producing = fields.Float('Produced Quantity', default=1.0, digits=dp.get_precision('Product Unit of Measure'))

    def button_record(self):
        wo = self.workorder_id
        wo.qty_producing = self.qty_producing
        wo.record_production()
        wo.end_previous()
        if wo.working_state != 'blocked' and wo.state == 'progress' and not wo.is_user_working:
            wo.button_start()
        return {'type': 'ir.actions.act_window_close'}