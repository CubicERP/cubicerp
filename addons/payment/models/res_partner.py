# coding: utf-8

from odoo import api, fields, models, exceptions, _

VALIDATION_CODE_DEFAULT = """# acc_number: char card number
# card: res.partner.bank object
# result = True : activate the constraint

#result = acc_number and acc_number[0]!='4'
#message = 'Wrong VISA card'"""

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
    sector_ids = fields.One2many("payment.address.sector", "bank_id", string="Address Sectors")
    validation = fields.Boolean("Python Validation", help="Python code to validate the account number format")
    validation_code = fields.Text("Validation Code", default=VALIDATION_CODE_DEFAULT)


class res_partner_bank(models.Model):
    _inherit = 'res.partner.bank'

    @api.depends('medium_type_id', 'medium_type_id.has_expiration')
    def _has_expiration(self):
        if self.medium_type_id:
            self.has_expiration = self.medium_type_id.has_expiration
        else:
            self.has_expiration = False
        self.sector_id = False
        self.bank_id = False
        self.acc_number = False

    medium_type_id = fields.Many2one("payment.medium.type", string="Medium Type")
    has_mandate = fields.Boolean("Has Mandate", related="medium_type_id.has_mandate")
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
    expiration_year = fields.Selection(lambda s:[(str(a),str(a)) for a in range(1997,int(fields.Date.today().split('-')[0])+7)],
                                       string="Expiration Year", default=lambda s: fields.Date.today().split('-')[0])
    require_number = fields.Boolean("Require Number", related="medium_type_id.require_number")
    has_owner = fields.Boolean("Has Owner", related="medium_type_id.has_owner")
    owner_id = fields.Many2one("res.partner", "Owner")
    has_address = fields.Boolean("Has Address", related="medium_type_id.has_address")
    address_id = fields.Many2one("res.partner", "Address")
    state_id = fields.Many2one("res.country.state", related="address_id.state_id", string="State")
    sector_id = fields.Many2one("payment.address.sector", string="Address Sector")
    has_calendar = fields.Boolean("Has Calendar", related="medium_type_id.has_calendar")
    calendar_id = fields.Many2one("resource.calendar", "Calendar")

    @api.constrains("acc_number", "bank_id")
    def validate_number(self):
        for card in self.filtered(lambda b: b.bank_id and b.bank_id.validation):
            localdict = {'acc_number': card.acc_number,
                         'card': card,
                         }
            exec(card.bank_id.validation_code, localdict)
            if localdict.get('result', False):
                raise exceptions.ValidationError(localdict.get('message',_("Card Number Wrong!")))

    @api.constrains("has_expiration", "expiration_month", "expiration_year")
    def validate_expiration(self):
        for card in self.filtered("has_expiration"):
            if "%s-%s-31"%(card.expiration_year, card.expiration_month) < fields.Date.today():
                raise exceptions.ValidationError(_("The card  is expired"))

    @api.depends("acc_number","medium_type_id","bank_name")
    def name_get(self):
        result = []
        for bank in self:
            name = "%s%s%s"%(bank.acc_number or '',bank.bank_name and ' [%s]'%bank.bank_name or '',bank.medium_type_id and ' (%s)'%bank.medium_type_id.name or '')
            result.append((bank.id, name))
        return result

    @api.onchange("sector_id")
    def on_change_sector(self):
        self.acc_number = self.sector_id.name
        self.bank_id = self.sector_id.bank_id.id