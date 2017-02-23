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

from openerp import models, api, fields, _


class SaleOrder(models.Model):
    _inherit = "sale.order"

    budget_move_ids = fields.One2many('budget.move', 'sale_id', string='Budget Transactions', readonly=True)

    @api.multi
    def action_wait(self):
        for sale in self:
            if sale.struct_id:
                tran = self.env['budget.move'].create_from_so(sale)
                tran.action_done()
        return super(SaleOrder,self).action_wait()

    @api.multi
    def action_cancel(self):
        for sale in self:
            sale.budget_move_ids.unlink()
        return super(SaleOrder,self).action_cancel()

