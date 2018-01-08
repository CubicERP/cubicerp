# coding: utf-8

from odoo import api, fields, models


class res_partner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    payment_token_ids = fields.One2many('payment.token', 'partner_id', 'Payment Tokens')
    payment_token_count = fields.Integer(
        'Count Payment Token', compute='_compute_payment_token_count')

    @api.depends('payment_token_ids')
    def _compute_payment_token_count(self):
        payment_data = self.env['payment.token'].read_group([
            ('partner_id', 'in', self.ids)], ['partner_id'], ['partner_id'])
        mapped_data = dict([(payment['partner_id'][0], payment['partner_id_count']) for payment in payment_data])
        for partner in self:
            partner.payment_token_count = mapped_data.get(partner.id, 0)

class res_bank(models.Model):
    _inherit = "res.bank"

    acquirer_ids = fields.Many2many("payment.acquirer", 'payment_acquirer_bank_rel', 'bank_id', 'acquirer_id', string="Acquirers")
    medium_type_ids = fields.Many2many("payment.medium.type", 'payment_medium_bank_rel', 'bank_id', 'medium_type_id', string="Medium Types")


class res_partner_bank(models.Model):
    _inherit = 'res.partner.bank'

    @api.depends('medium_type_id', 'medium_type_id.has_expiration')
    def _has_expiration(self):
        if self.medium_type_id:
            self.has_expiration = self.medium_type_id.has_expiration
        else:
            self.has_expiration = False

    medium_type_id = fields.Many2one("payment.medium.type", string="Medium Type")
    has_expiration = fields.Boolean("Has Expiration Date", compute=_has_expiration)
    expiration_month = fields.Selection([('01', '01'),
                                         ('02', '02'),
                                         ('03', '03'),
                                         ('04', '04'),
                                         ('05', '05'),
                                         ('06', '06'),
                                         ('07', '07'),
                                         ('08', '08'),
                                         ('09', '09'),
                                         ('10', '10'),
                                         ('11', '11'),
                                         ('12', '12')], string="Expiration Month")
    expiration_year = fields.Char("Expiration Year", size=4)