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

class MrpProductionSchedule(models.TransientModel):
    _name = 'mrp.production.schedule'

    type = fields.Selection([('auto','Automatic'),
                             ('spec','Specific Start date')], default='auto', required=True)
    start_date = fields.Datetime()

    def button_plan(self):
        ctx = self._context.copy()
        if self.type == 'spec':
            ctx['force_start_date'] = self.start_date
        self.env['mrp.production'].browse(ctx.get('active_ids',[])).with_context(ctx).button_plan()
        return {}