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

from openerp import models, fields, api


class payment_kind(models.Model):
    _name = 'payment.kind'
    _description = "Payment Kind"

    name = fields.Char("Name", required=True)
    medium_ids = fields.Many2many("payment.medium", "payment_medium_kind_rel", "kind_id", "medium_id", string="Mediums")
    active = fields.Boolean("Active", default=True)


class payment_medium(models.Model):
    _name = 'payment.medium'
    _description = "Payment Medium. Merchant bank to process the payments"

    name = fields.Char("Name", required=True)
    kind_ids = fields.Many2many("payment.kind", "payment_medium_kind_rel", "medium_id", "kind_id", string="Kinds")
    analytic_ids = fields.Many2many("account.analytic.account", "payment_medium_analytic_rel", "medium_id", "analytic_id", string="Analytic Accounts")
    active = fields.Boolean("Active", default=True)


class payment_mode(models.Model):
    _name= 'payment.mode'
    _description= 'Payment Mode'

    name = fields.Char('Name', required=True, help='Mode of Payment')
    bank_id = fields.Many2one('res.partner.bank', "Bank account", required=True,help='Bank Account for the Payment Mode')
    journal = fields.Many2one('account.journal', 'Journal', required=True, domain=[('type', 'in', ('bank','cash'))],
                              help='Bank or Cash Journal for the Payment Mode')
    company_id = fields.Many2one('res.company', 'Company',required=True, default= lambda self: self.env.user.company_id.id)
    partner_id = fields.Many2one('res.partner', related='company_id.partner_id', string='Partner', store=True)
    account_id = fields.Many2one('account.account', 'Account', required=True, domain=[('type','=','payable')],
                                 help="Account to make a group for massive payments")
    analytic_id = fields.Many2one('account.analytic.account', 'Analytic Account', domain=[('type', '!=', 'view')])

    def suitable_bank_types(self, cr, uid, payment_code=None, context=None):
        """Return the codes of the bank type that are suitable
        for the given payment type code"""
        if not payment_code:
            return []
        cr.execute(""" SELECT pb.state
            FROM res_partner_bank pb
            JOIN payment_mode pm ON (pm.bank_id = pb.id)
            WHERE pm.id = %s """, [payment_code])
        return [x[0] for x in cr.fetchall()]

    @api.onchange('company_id')
    def onchange_company_id (self):
        result = {}
        if self.company_id:
            partner_id = self.company_id.partner_id.id
            result['partner_id'] = partner_id
        return {'value': result}
