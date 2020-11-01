# -*- coding: utf-8 -*-
##############################################################################
#
#    Cubic ERP, Enterprise and Government Management Software
#    Copyright (C) 2020 Cubic ERP & Teradata SAC (<http://cubicerp.com>).
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

from odoo import fields, models, exceptions, _

class AccountMove(models.Model):
    _inherit = "account.move"

    landed_cost_id = fields.Many2one("stock.landed.cost")


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    landed_cost_ids = fields.Many2many("stock.landed.cost", 'stock_landed_cost_invoice_rel', 'invoice_id', 'cost_id')


    def action_invoice_open(self):
        res = super(AccountInvoice, self).action_invoice_open()
        for invoice in self:
            costs = invoice.invoice_line_ids.mapped('purchase_id').mapped('landed_cost_id')
            for cost in costs:
                cost.invoice_ids |= invoice
        return res

    def action_invoice_cancel(self):
        res = super(AccountInvoice, self).action_invoice_cancel()
        if self.mapped('landed_cost_ids').filtered(lambda c: c.state == 'done'):
            raise exceptions.ValidationError(_("The landed cost %s must not be in done state") % (
                ', '.join([c.name for c in self.mapped('landed_cost_ids').filtered(lambda c: c.state == 'done')])))
        return res