# -*- encoding: utf-8 -*-
##############################################################################
#
#    Branch Cubic ERP, Enterprise Management Software
#    Copyright (C) 2013 Cubic ERP - Teradata SAC (<http://cubicerp.com>).
#
#    This program can only be used with a valid Branch Cubic ERP agreement,
#    it is forbidden to publish, distribute, modify, sublicense or sell 
#    copies of the program.
#
#    The adove copyright notice must be included in all copies or 
#    substancial portions of the program.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT WARRANTY OF ANY KIND; without even the implied warranty
#    of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
##############################################################################

from openerp import models, fields, api
import openerp.addons.decimal_precision as dp


class account_invoice(models.Model):
    _name = 'account.invoice'
    _inherit = 'account.invoice'

    amount_text = fields.Char(string='Amount in text', compute='_convert')
    picking = fields.Char(string='Picking number', compute='_get_pickings')
    discount_total = fields.Float(string='Discount total', digits=dp.get_precision('Account'),
                                  compute='_get_discount_total')

    def divide(self, n, d):
        return (n / d)

    def convert(self, amount, currency):
        return self.pool.get('ir.translation').amount_to_text(amount, self.company_id.country_id.code.lower() or 'pe',
                                                              currency or 'Nuevo Sol')

    def day(self, date):
        return self.pool.get('ir.translation').date_part(date, 'day', format='number',
                                                         lang=self.company_id.country_id.code.lower() or 'pe')

    def month(self, date):
        return self.pool.get('ir.translation').date_part(date, 'month', format='text',
                                                         lang=self.company_id.country_id.code.lower() or 'pe')

    def year(self, date):
        return self.pool.get('ir.translation').date_part(date, 'year', format='number',
                                                         lang=self.company_id.country_id.code.lower() or 'pe')

    def get_pickings(self, invoice_id):
        res = ''
        sale_obj = self.env['sale.order']
        self._cr.execute('select order_id from sale_order_invoice_rel where invoice_id=%s' % (invoice_id))
        order_ids = self._cr.fetchall()
        sale_ids = []
        for order in order_ids:
            sale_ids.append(order[0])

        for sale in sale_obj.browse(sale_ids):
            for picking in sale.picking_ids:
                res += picking.name + ' / '
        if res[-3:] == ' / ': res = res[:-3]
        return res

    @api.one
    @api.depends('amount_total', 'currency_id')
    def _convert(self):
        currency = self.currency_id.long_name or self.currency_id.name
        country_code = 'pe'
        if self.company_id.country_id and self.company_id.country_id.code:
            country_code = self.company_id.country_id.code.lower()
        if currency == "USD":
            currency = " DOLARES AMERICANOS"
        elif currency == "EUR":
            currency = " EUROS"
        elif currency == "PEN":
            currency = " SOLES"
        self.amount_text = self.pool.get('ir.translation').amount_to_text(self.amount_total, country_code, currency)

    @api.one
    def _get_pickings(self):
        res = ''
        sale_obj = self.env['sale.order']
        self._cr.execute('select order_id from sale_order_invoice_rel where invoice_id=%s' % (self.id))
        order_ids = self._cr.fetchall()
        sale_ids = []
        for order in order_ids:
            sale_ids.append(order[0])

        for sale in sale_obj.browse(sale_ids):
            for picking in sale.picking_ids:
                res += picking.name + ' / '
                if res[-3:] == ' / ': res = res[:-3]
                self.picking = res

    @api.one
    @api.depends('invoice_line')
    def _get_discount_total(self):
        res = 0.0
        for line in self.invoice_line:
            res += (line.price_unit * line.discount / 100) * line.quantity
        amount = self.currency_id.round(res)
        self.discount_total = amount

class account_invoice_line(models.Model):
    _inherit = 'account.invoice.line'

    discount_amount=fields.Float(string='Discount Amount', digits=dp.get_precision('Account'), compute='_get_discount_amount')

    @api.one
    @api.depends('price_unit', 'discount', 'quantity')
    def _get_discount_amount(self):
        self.discount_amount=self.invoice_id.currency_id.round((self.price_unit*self.discount/100)*self.quantity)

