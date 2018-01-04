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

from odoo import api, models, _, fields
from odoo.tools.sql import drop_view_if_exists
from odoo.addons import decimal_precision as dp


class AccountEntriesReport(models.Model):
    _name = "account.entries.report"
    _description = "Journal Items Analysis"
    _auto = False
    _rec_name = 'date_effective'
    
    date_effective = fields.Date('Effective Date', readonly=True)
    date_created = fields.Date('Date Created', readonly=True)
    date_maturity = fields.Date('Date Maturity', readonly=True)
    ref = fields.Char('Reference', readonly=True)
    note = fields.Char('Detail', readonly=True)
    nbr = fields.Integer('# of Items', readonly=True)
    debit = fields.Float('Debit', readonly=True)
    credit = fields.Float('Credit', readonly=True)
    balance = fields.Float('Balance', readonly=True)
    currency_id = fields.Many2one('res.currency', 'Currency', readonly=True)
    amount_currency = fields.Float('Amount Currency', digits_compute=dp.get_precision('Account'), readonly=True)
    period_id = fields.Many2one('account.period', 'Period', readonly=True)
    account_id = fields.Many2one('account.account', 'Account', readonly=True)
    parent_account_id = fields.Many2one('account.account', 'Parent Account', readonly=True)
    journal_id = fields.Many2one('account.journal', 'Journal', readonly=True)
    journal_type = fields.Selection([
            ('regular', 'Regular Operations'),
            ('opening', 'Opening Fiscal Year'),
            ('shutdown', 'Shutdown Fiscal Year'),
        ], string="Journal Type")
    product_id = fields.Many2one('product.product', 'Product', readonly=True)
    product_uom_id = fields.Many2one('product.uom', 'Product Unit of Measure', readonly=True)
    move_state = fields.Selection([('draft','Unposted'), ('posted','Posted')], 'Status', readonly=True)
    reconcile_id = fields.Many2one('account.move.reconcile', 'Reconciliation number', readonly=True)
    partner_id = fields.Many2one('res.partner','Partner', readonly=True)
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account', readonly=True)
    product_quantity = fields.Float('Products Quantity', digits=(16,2), readonly=True)
    user_type = fields.Many2one('account.account.type', 'Account Type', readonly=True)
    report_type = fields.Many2one('account.financial.report', 'Financial Report', readonly=True)
    chart_account = fields.Many2one('account.group', 'Chart Account', readonly=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True)


    _order = 'date_effective desc'

    def _get_select(self):
        return ''

    def _get_from(self):
        return ''

    def _get_where(self):
        return ''

    @api.model_cr
    def init(self):
        drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            create or replace view account_entries_report as (
            select
                l.id as id,
                am.date as date_effective,
                l.date_maturity as date_maturity,
                coalesce(am.ref,am.name) as ref,
                l.name as note,
                am.state as move_state,
                l.full_reconcile_id as reconcile_id,
                l.partner_id as partner_id,
                l.product_id as product_id,
                l.product_uom_id as product_uom_id,
                am.company_id as company_id,
                am.journal_id as journal_id,
                case when aj.type = 'opening' then 'opening' when aj.type = 'closing' then 'shutdown' else 'regular' end as journal_type,
                l.account_id as account_id,
                a.group_id as parent_account_id,
                l.analytic_account_id as analytic_account_id,
                a.user_type_id as user_type,
                at.financial_report_id as report_type,
                a.chart_account_id as chart_account,
                1 as nbr,
                l.quantity as product_quantity,
                l.currency_id as currency_id,
                l.amount_currency as amount_currency,
                l.debit as debit,
                l.credit as credit,
                coalesce(l.debit, 0.0) - coalesce(l.credit, 0.0) as balance
                %s
            from
                account_move_line l
                inner join account_account a on (l.account_id = a.id)
                inner join account_move am on (am.id=l.move_id)
                inner join account_journal aj on (aj.id=am.journal_id)
                left join account_account_type at on (a.user_type_id = at.id)
                
                %s
                where l.id > 0
                %s
            )
        """%(self._get_select(),self._get_from(),self._get_where()))
