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

from openerp import fields, models

class product_category(models.Model):
    _inherit = "product.category"

    property_account_income_categ = fields.Many2one('account.account', string="Income Account", company_dependent = True,
                                                    help="This account will be used for invoices to value sales.")

    property_account_expense_categ = fields.Many2one('account.account', string="Expense Account", company_dependent = True,
                                                     help="This account will be used for invoices to value expenses.")


class product_template(models.Model):
    _inherit = "product.template"

    taxes_id = fields.Many2many('account.tax', 'product_taxes_rel', 'prod_id', 'tax_id', 'Customer Taxes',
                                company_dependent=True, domain=[('parent_id','=',False),('type_tax_use','in',['sale','all'])])
    supplier_taxes_id = fields.Many2many('account.tax', 'product_supplier_taxes_rel', 'prod_id', 'tax_id', 'Supplier Taxes',
                                         company_dependent=True, domain=[('parent_id', '=', False),('type_tax_use','in',['purchase','all'])])
    property_account_income = fields.Many2one('account.account', string="Income Account", company_dependent = True,
            help="This account will be used for invoices instead of the default one to value sales for the current product.")
    property_account_expense = fields.Many2one('account.account', string="Expense Account", company_dependent = True,
            help="This account will be used for invoices instead of the default one to value expenses for the current product.")
