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

from openerp import models, fields, api, _


class AssignBudgetPeriod(models.Model):
    """
    For Chart of Struct
    """
    _name = "assign.budget.period"
    _description = "Assign Budget Period"

    period_id = fields.Many2one('budget.period', string='Budget Period')

    @api.model
    def domain_account_period(self):
        return [
            ('id', 'in', (self.get_account_period_ids()).ids)
        ]

    @api.model
    def default_account_period_ids(self):
        return self.get_account_period_ids()

    account_period_ids = fields.Many2many('account.period', 'account_periods_account_period_rel_',
                                          'account_period_ids', 'account_period', 'Account Periods',
                                          domain=domain_account_period,
                                          default=default_account_period_ids,
                                          )

    @api.model
    def get_account_period_ids(self):
        return self.env['account.period'].browse(self._context.get('active_ids', None))

    @api.multi
    def to_assign_account_period(self):
        self.ensure_one()
        self.account_period_ids.write({'budget_period_id': self.period_id.id})

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
