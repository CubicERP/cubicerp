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


class PostBudgetMove(models.TransientModel):
    _name = "post.budget.move"
    _description = "Post Budget Move"

    @api.model
    def domain_budget_move_ids(self):
        return [
            ('id', 'in', (self.get_budget_move_ids()).ids)
        ]

    @api.model
    def default_budget_move_ids(self):
        return self.get_budget_move_ids()

    budget_move_ids = fields.Many2many('budget.move', 'budget_move_ids_budget_move_rel_',
                                          'budget_move_ids', 'budget_move', 'Budget Move',
                                          domain=domain_budget_move_ids,
                                          default=default_budget_move_ids,
                                          )

    @api.model
    def get_budget_move_ids(self):
        """

        :return: the account.period selected to set their budget.period
        """
        return self.env['budget.move'].browse(self._context.get('active_ids', None))

    @api.multi
    def multi_post_budget_move(self):
        self.ensure_one()
        for move in self.budget_move_ids:
            move.action_done()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
