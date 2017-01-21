# -*- coding: utf-8 -*-
##############################################################################
#
#    Cubic ERP, Enterprise Management Software
#    Copyright (C) 2017 Cubic ERP - Teradata SAC (<http://cubicerp.com>).
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

from openerp import models, fields, api, exceptions, _

class BudgetMove(models.Model):
    _name = "budget.move"
    _description = "Budget Move Transaction"

    @api.model
    def _get_period(self):
        periods = self.env['budget.period'].find()
        return periods and periods[0] or False

    name = fields.Char("Name", required=True, default="/", states={'draft': [('readonly', False)]}, readonly=True)
    ref = fields.Char("Reference", states={'draft': [('readonly', False)]}, readonly=True)
    date = fields.Date("Date", required=True, default=fields.Date.today, states={'draft': [('readonly', False)]}, readonly=True)
    period_id = fields.Many2one('budget.period', string="Period", required=True, default=_get_period,
                                states={'draft': [('readonly', False)]}, readonly=True)
    line_ids = fields.One2many('budget.move.line', 'move_id', string="Lines", states={'draft': [('readonly', False)]}, readonly=True)
    move_line_id = fields.Many2one('account.move.line', string="Move Line",
                                states={'draft': [('readonly', False)]}, readonly=True)
    state = fields.Selection([('draft','Draft'),
                              ('done','Done')], string="State", readonly=True, default='draft')

    @api.model
    def create(self, vals):
        if vals.get('name') == '/':
            vals['name'] = self.env['ir.sequence'].get('budget.control.move')
        return super(BudgetMove, self).create(vals)

class BudgetMoveLine(models.Model):
    _name = "budget.move.line"
    _description = "Budget Move Line"

    name = fields.Char("Name", required=True)
    move_id = fields.Many2one("budget.move", string="Move", required=True, ondelete="cascade")
    period_id = fields.Many2one('budget.period', string="Period", related="move_id.period_id", readonly=True, store=True)
    struct_id = fields.Many2one('budget.struct', string="Struct", required=True)
    analytic_id = fields.Many2one('account.analytic.account', string="Analytic Account")
    partner_id = fields.Many2one('res.partner', string="Partner")
    available = fields.Float("Available")
    committed = fields.Float("Committed")
    provision = fields.Float("Provision")
    paid = fields.Float("Paid")
