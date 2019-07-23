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
import requests

class res_currency(models.Model):
    _inherit = "res.currency"

    pe_update_all = fields.Boolean("Update All", default=True,
                                   help="Update all peruvian USD rates. This option not override the existing rates")

    @api.model
    def pe_update_usd(self):
        self.env.ref('base.PEN').pe_update()

    @api.multi
    def get_pe_currency(self):
        return self

    @api.multi
    def pe_update(self):
        for currency in self.get_pe_currency():
            if currency.pe_update_all:
                rates = self.get_pe_rates()
                fechas = tuple(["%s 08:00:00"%r['fecha'] for r in rates])
                dfechas = set([r.name for r in self.env['res.currency.rate'].search([('currency_id', '=', self.id),
                                                                                 ('name', 'in', fechas)])])
                for rate in rates:
                    if not rate['fecha'] in dfechas:
                        currency.set_pe_rate(rate)
                currency.pe_update_all = False
            else:
                self.set_pe_rate(self.get_pe_rate())

    def set_pe_rate(self, rate):
        res = False
        if not self.rate_ids.filtered(lambda r: r.name[:10] == rate['fecha']):
            res = self.env['res.currency.rate'].create(self._currency_rate_dict(rate))
        return res

    def _currency_rate_dict(self, rate):
        return {'name': "%s 08:00:00"%rate['fecha'],
                'rate': rate['venta'],
                'currency_id': self.id}

    @api.model
    def get_pe_rate(self):
        return requests.get('%s/tasa/USD' % (self.env['ir.config_parameter'].sudo().get_param('pe_api.url') or "http://api.cubicerp.com/pe"),
                            headers={'Content-Type': 'application/json'},
                            data='{"params":{"vat":"%s","dbid":"%s"}}' % (
                                self.env.user.company_id.vat,
                                self.env['ir.config_parameter'].sudo().get_param('database.uuid'))
                            ).json().get('result', {})

    @api.model
    def get_pe_rates(self):
        fecha = fields.Date.today()
        fecha_inicio = "%s-01-01" % (int(fecha[:4]) - 1)
        return requests.get('%s/tasa/USD' % (self.env['ir.config_parameter'].sudo().get_param('pe_api.url') or "http://api.cubicerp.com/pe"),
                            headers={'Content-Type': 'application/json'},
                            data='{"params":{"fecha":"%s","fecha_inicio":"%s","vat":"%s","dbid":"%s"}}' % (
                                fecha, fecha_inicio, self.env.user.company_id.vat,
                                self.env['ir.config_parameter'].sudo().get_param('database.uuid'))
                            ).json().get('result', [])
