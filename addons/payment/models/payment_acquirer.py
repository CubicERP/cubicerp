# -*- coding: utf-'8' "-*-"

import logging
from openerp import models, fields, api, exceptions, _, SUPERUSER_ID
from openerp.tools import float_round, float_repr, float_compare

_logger = logging.getLogger(__name__)


def _partner_format_address(address1=False, address2=False):
    return ' '.join((address1 or '', address2 or '')).strip()


def _partner_split_name(partner_name):
    return [' '.join(partner_name.split()[:-1]), ' '.join(partner_name.split()[-1:])]


class ValidationError(ValueError):
    """ Used for value error when validating transaction data coming from acquirers. """
    pass


class PaymentAcquirer(models.Model):
    """ Acquirer Model. Each specific acquirer can extend the model by adding
    its own fields, using the acquirer_name as a prefix for the new fields.

    Each acquirer has a link to an ir.ui.view record that is a template of
    a button used to display the payment form. See examples in ``payment_ogone``
    and ``payment_paypal`` modules.

    Methods that should be added in an acquirer-specific implementation:

     - ``<name>_form_generate_values(self, cr, uid, id, reference, amount, currency,
       partner_id=False, partner_values=None, tx_custom_values=None, context=None)``:
       method that generates the values used to render the form button template.
     - ``<name>_get_form_action_url(self, cr, uid, id, context=None):``: method
       that returns the url of the button form. It is used for example in
       ecommerce application, if you want to post some data to the acquirer.
     - ``<name>_compute_fees(self, cr, uid, id, amount, currency_id, country_id,
       context=None)``: computed the fees of the acquirer, using generic fields
       defined on the acquirer model (see fields definition).

    Each acquirer should also define controllers to handle communication between
    OpenERP and the acquirer. It generally consists in return urls given to the
    button form and that the acquirer uses to send the customer back after the
    transaction, with transaction details given as a POST request.
    """
    _name = 'payment.acquirer'
    _description = 'Payment Acquirer with data for electronic payments'

    def _get_providers(self, cr, uid, context=None):
        return []

    # indirection to ease inheritance
    _provider_selection = lambda self, *args, **kwargs: self._get_providers(*args, **kwargs)

    name = fields.Char('Name', required=True, translate=True)
    medium_id = fields.Many2one('payment.medium' ,string= "Medium")
    provider = fields.Selection(_provider_selection, string='Electronic Provider', required=True)
    sequence_id = fields.Many2one("ir.sequence", "Transaction Sequence")
    company_id = fields.Many2one('res.company', 'Company', required=True, default=lambda self:self.env.user.company_id)
    pre_msg = fields.Html('Message', translate=True, help='Message displayed to explain and help the payment process.')
    post_msg = fields.Html('Thanks Message', help='Message displayed after having done the payment process.')
    validation = fields.Selection([('manual', 'Manual'),
                                ('automatic', 'Automatic')], string='Process Method', default='automatic',
                               help='Static payments are payments like transfer, that require manual steps.')
    view_template_id = fields.Many2one('ir.ui.view', 'Form Button Template', required=True)
    environment = fields.Selection([('test', 'Test'), ('prod', 'Production')], string='Environment', default='test', oldname='env')
    website_published = fields.Boolean('Visible in Portal / Website', copy=False,
                                    help="Make this payment acquirer available (Customer invoices, etc.)")
    # Fees
    fees_active = fields.Boolean('Compute fees')
    fees_dom_fixed = fields.Float('Fixed domestic fees')
    fees_dom_var = fields.Float('Variable domestic fees (in percents)')
    fees_int_fixed = fields.Float('Fixed international fees')
    fees_int_var = fields.Float('Variable international fees (in percents)')
    sequence = fields.Integer("Priority", default=5)

    _order = "sequence"

    @api.multi
    def name_get(self):
        return [(a.id, "%s [%s]" % (a.name, a.medium_id.name)) for a in self]

    def get_form_action_url(self, cr, uid, id, context=None):
        """ Returns the form action URL, for form-based acquirer implementations. """
        acquirer = self.browse(cr, uid, id, context=context)
        if hasattr(self, '%s_get_form_action_url' % acquirer.provider):
            return getattr(self, '%s_get_form_action_url' % acquirer.provider)(cr, uid, id, context=context)
        return False

    def form_preprocess_values(self, cr, uid, id, reference, amount, currency_id, tx_id, partner_id, partner_values, tx_values, context=None):
        """  Pre process values before giving them to the acquirer-specific render
        methods. Those methods will receive:

             - partner_values: will contain name, lang, email, zip, address, city,
               country_id (int or False), country (browse or False), phone, reference
             - tx_values: will contain reference, amount, currency_id (int or False),
               currency (browse or False), partner (browse or False)
        """
        acquirer = self.browse(cr, uid, id, context=context)

        if tx_id:
            tx = self.pool['payment.transaction'].browse(cr, uid, tx_id, context=context)
            tx_data = {
             'reference': tx.reference,
             'amount': tx.amount,
             'currency_id': tx.currency_id.id,
             'currency': tx.currency_id,
             'partner': tx.partner_id,
            }
            partner_data = {
             'name': tx.partner_name,
             'lang': tx.partner_lang,
             'email': tx.partner_email,
             'zip': tx.partner_zip,
             'address': tx.partner_address,
             'city': tx.partner_city,
             'country_id': tx.partner_country_id.id,
             'country': tx.partner_country_id,
             'phone': tx.partner_phone,
             'reference': tx.partner_reference,
             'state': None,
            }
        else:
            if partner_id:
                partner = self.pool['res.partner'].browse(cr, uid, partner_id, context=context)
                partner_data = {
                 'name': partner.name,
                 'lang': partner.lang,
                 'email': partner.email,
                 'zip': partner.zip,
                 'city': partner.city,
                 'address': _partner_format_address(partner.street, partner.street2),
                 'country_id': partner.country_id.id,
                 'country': partner.country_id,
                 'phone': partner.phone,
                 'state': partner.state_id,
                }
            else:
                partner, partner_data = False, {}
            partner_data.update(partner_values)

            if currency_id:
                currency = self.pool['res.currency'].browse(cr, uid, currency_id, context=context)
            else:
                currency = self.pool['res.users'].browse(cr, uid, uid, context=context).company_id.currency_id
            tx_data = {
             'reference': reference,
             'amount': amount,
             'currency_id': currency.id,
             'currency': currency,
             'partner': partner,
            }

        # update tx values
        tx_data.update(tx_values)

        # update partner values
        if not partner_data.get('address'):
            partner_data['address'] = _partner_format_address(partner_data.get('street', ''), partner_data.get('street2', ''))
        if not partner_data.get('country') and partner_data.get('country_id'):
            partner_data['country'] = self.pool['res.country'].browse(cr, uid, partner_data.get('country_id'), context=context)
        partner_data.update({
         'first_name': _partner_split_name(partner_data['name'])[0],
         'last_name': _partner_split_name(partner_data['name'])[1],
        })

        # compute fees
        fees_method_name = '%s_compute_fees' % acquirer.provider
        if hasattr(self, fees_method_name):
            fees = getattr(self, fees_method_name)(
                cr, uid, id, tx_data['amount'], tx_data['currency_id'], partner_data['country_id'], context=None)
            tx_data['fees'] = float_round(fees, 2)

        return (partner_data, tx_data)

    def render(self, cr, uid, id, reference, amount, currency_id, tx_id=None, partner_id=False, partner_values=None, tx_values=None, context=None):
        """ Renders the form template of the given acquirer as a qWeb template.
        All templates will receive:

         - acquirer: the payment.acquirer browse record
         - user: the current user browse record
         - currency_id: id of the transaction currency
         - amount: amount of the transaction
         - reference: reference of the transaction
         - partner: the current partner browse record, if any (not necessarily set)
         - partner_values: a dictionary of partner-related values
         - tx_values: a dictionary of transaction related values that depends on
                      the acquirer. Some specific keys should be managed in each
                      provider, depending on the features it offers:

          - 'feedback_url': feedback URL, controler that manage answer of the acquirer
                            (without base url) -> FIXME
          - 'return_url': URL for coming back after payment validation (wihout
                          base url) -> FIXME
          - 'cancel_url': URL if the client cancels the payment -> FIXME
          - 'error_url': URL if there is an issue with the payment -> FIXME

         - context: OpenERP context dictionary

        :param string reference: the transaction reference
        :param float amount: the amount the buyer has to pay
        :param res.currency browse record currency: currency
        :param int tx_id: id of a transaction; if set, bypasses all other given
                          values and only render the already-stored transaction
        :param res.partner browse record partner_id: the buyer
        :param dict partner_values: a dictionary of values for the buyer (see above)
        :param dict tx_custom_values: a dictionary of values for the transction
                                      that is given to the acquirer-specific method
                                      generating the form values
        :param dict context: OpenERP context
        """
        if context is None:
            context = {}
        if tx_values is None:
            tx_values = {}
        if partner_values is None:
            partner_values = {}
        acquirer = self.browse(cr, uid, id, context=context)

        # pre-process values
        amount = float_round(amount, 2)
        partner_values, tx_values = self.form_preprocess_values(
            cr, uid, id, reference, amount, currency_id, tx_id, partner_id,
            partner_values, tx_values, context=context)

        # call <name>_form_generate_values to update the tx dict with acqurier specific values
        cust_method_name = '%s_form_generate_values' % (acquirer.provider)
        if hasattr(self, cust_method_name):
            method = getattr(self, cust_method_name)
            partner_values, tx_values = method(cr, uid, id, partner_values, tx_values, context=context)

        qweb_context = {
         'tx_url': context.get('tx_url', self.get_form_action_url(cr, uid, id, context=context)),
         'submit_class': context.get('submit_class', 'btn btn-link'),
         'submit_txt': context.get('submit_txt'),
         'acquirer': acquirer,
         'user': self.pool["res.users"].browse(cr, uid, uid, context=context),
         'reference': tx_values['reference'],
         'amount': tx_values['amount'],
         'currency': tx_values['currency'],
         'partner': tx_values.get('partner'),
         'partner_values': partner_values,
         'tx_values': tx_values,
         'context': context,
        }

        # because render accepts view ids but not qweb -> need to use the xml_id
        return self.pool['ir.ui.view'].render(cr, uid, acquirer.view_template_id.xml_id, qweb_context, engine='ir.qweb', context=context)

    def _wrap_payment_block(self, cr, uid, html_block, amount, currency_id, context=None):
        payment_header = _('Pay safely online')
        amount_str = float_repr(amount, self.pool['decimal.precision'].precision_get(cr, uid, 'Account'))
        currency = self.pool['res.currency'].browse(cr, uid, currency_id, context=context)
        currency_str = currency.symbol or currency.name
        amount = u"%s %s" % ((currency_str, amount_str) if currency.position == 'before' else (amount_str, currency_str))
        result = u"""<div class="payment_acquirers">
                         <div class="payment_header">
                             <div class="payment_amount">%s</div>
                             %s
                         </div>
                         %%s
                     </div>""" % (amount, payment_header)
        return result % html_block.decode("utf-8")

    def render_payment_block(self, cr, uid, reference, amount, currency_id, tx_id=None, partner_id=False, partner_values=None, tx_values=None, company_id=None, context=None):
        html_forms = []
        domain = [('website_published', '=', True), ('validation', '=', 'automatic')]
        if company_id:
            domain.append(('company_id', '=', company_id))
        acquirer_ids = self.search(cr, uid, domain, context=context)
        for acquirer_id in acquirer_ids:
            button = self.render(
                cr, uid, acquirer_id,
                reference, amount, currency_id,
                tx_id, partner_id, partner_values, tx_values,
                context)
            html_forms.append(button)
        if not html_forms:
            return ''
        html_block = '\n'.join(filter(None, html_forms))
        return self._wrap_payment_block(cr, uid, html_block, amount, currency_id, context=context)


class PaymentTransaction(models.Model):
    """ Transaction Model. Each specific acquirer can extend the model by adding
    its own fields.

    Methods that can be added in an acquirer-specific implementation:

     - ``<name>_create``: method receiving values used when creating a new
       transaction and that returns a dictionary that will update those values.
       This method can be used to tweak some transaction values.

    Methods defined for convention, depending on your controllers:

     - ``<name>_form_feedback(self, cr, uid, data, context=None)``: method that
       handles the data coming from the acquirer after the transaction. It will
       generally receives data posted by the acquirer after the transaction.
    """
    _name = 'payment.transaction'
    _description = 'Electronic Payment Transaction'
    _inherit = ['mail.thread']
    _order = 'id desc'
    _rec_name = 'reference'

    date_create = fields.Datetime('Date', required=True, default=fields.Datetime.now, readonly=True, states={'draft': [('readonly', False)]})
    date_validate = fields.Datetime('Validation Date', readonly=True, states={'draft': [('readonly', False)]})
    acquirer_id = fields.Many2one('payment.acquirer', 'Acquirer', required=True, readonly=True, states={'draft': [('readonly', False)]})
    medium_id = fields.Many2one("payment.medium", string="Medium", related="acquirer_id.medium_id", readonly=True)
    type = fields.Selection([('server2server', 'Server To Server'),
                              ('form', 'Form'),
                              ('server2file', 'Server To/From File')], string='Type', required=True, default='form',
                            readonly=True, states={'draft': [('readonly', False)]})
    state = fields.Selection([('draft', 'Draft'),
                           ('pending', 'Pending'),
                           ('done', 'Done'),
                           ('error', 'Error'),
                           ('cancel', 'Canceled')], 'Status', required=True, track_visibility='onchange', copy=False,
                             default='draft', readonly=True)
    state_message = fields.Text('Message', help='Field used to store error and/or validation messages for information',
                                readonly=True, states={'draft': [('readonly', False)]})
    # payment
    amount = fields.Float('Amount', required=True, digits=(16, 2), track_visibility='always', help='Amount in cents',
                          readonly=True, states={'draft': [('readonly', False)]})
    fees = fields.Float('Fees', digits=(16, 2), track_visibility='always', readonly=True, states={'draft': [('readonly', False)]},
                        help='Fees amount; set by the system because depends on the acquirer')
    bank_statement_id = fields.Many2one("account.bank.statement", string="Bank Statement", states={'done': [('readonly', True)], 'cancel': [('readonly', True)], 'error': [('readonly', True)]})
    reconcile = fields.Selection([('partial', 'Partial'),
                                  ('total', 'Total')], string="Reconciliation", required=True, default='total',
                                 states={'done': [('readonly', True)], 'cancel': [('readonly', True)], 'error': [('readonly', True)]})
    currency_id = fields.Many2one('res.currency', 'Currency', required=True, readonly=True, states={'draft': [('readonly', False)]},
                                  default=lambda self: self.env.user.company_id.currency_id.id)
    reference = fields.Char('Transaction Number', required=True, readonly=True, states={'draft': [('readonly', False)]},
                            help="Use slash '/' to make a automatic sequence number")
    acquirer_reference = fields.Char('Acquirer Order Reference', help='Reference of the TX as stored in the acquirer database',
                                     readonly=True, states={'draft': [('readonly', False)]})
    invoice_ids = fields.Many2many('account.invoice', 'payment_transaction_invoice_rel', 'transaction_id', 'invoice_id',
                                   string="Invoices", readonly=True, states={'draft': [('readonly', False)]})
    statement_ids = fields.Many2many('account.bank.statement.line', 'payment_transaction_statement_rel',
                                     'transaction_id', 'statement_id', string="Statement Lines", readonly=True,
                                     states={'draft': [('readonly', False)], 'pending': [('readonly', False)]})
    # duplicate partner / transaction data to store the values at transaction time
    partner_id = fields.Many2one('res.partner', 'Partner', track_visibility='onchange', readonly=True, states={'draft': [('readonly', False)]})
    partner_name = fields.Char('Partner Name', readonly=True, states={'draft': [('readonly', False)]})
    partner_lang = fields.Char('Lang', readonly=True, states={'draft': [('readonly', False)]})
    partner_email = fields.Char('Email', readonly=True, states={'draft': [('readonly', False)]})
    partner_zip = fields.Char('Zip', readonly=True, states={'draft': [('readonly', False)]})
    partner_address = fields.Char('Address', readonly=True, states={'draft': [('readonly', False)]})
    partner_city = fields.Char('City', readonly=True, states={'draft': [('readonly', False)]})
    partner_country_id = fields.Many2one('res.country', 'Country', readonly=True, states={'draft': [('readonly', False)]})
    partner_phone = fields.Char('Phone', readonly=True, states={'draft': [('readonly', False)]})
    partner_reference = fields.Char('Partner Reference', readonly=True, states={'draft': [('readonly', False)]},
                                    help='Reference of the customer in the acquirer database')

    @api.constrains('reference', 'state')
    def _check_reference(self, cr, uid, ids, context=None):
        transaction = self.browse(cr, uid, ids[0], context=context)
        if transaction.state not in ['cancel', 'error']:
            if self.search(cr, uid, [('reference', '=', transaction.reference), ('id', '!=', transaction.id)], context=context, count=True):
                raise exceptions.ValidationError('The payment transaction reference must be unique!')
        return True

    @api.cr_uid_context
    def create(self, cr, uid, values, context=None):
        Acquirer = self.pool['payment.acquirer']

        if values.get('partner_id'):
            partner = self.on_change_partner_id(cr, uid, None, values.get('partner_id'), context=context)['values']
            for field in ['partner_name', 'partner_lang', 'partner_email', 'partner_zip', 'partner_address',
                          'partner_city', 'partner_country_id', 'partner_phone', 'partner_reference']:
                if not values.get(field):
                    values[field] = partner.get(field)

        # call custom create method if defined (i.e. ogone_create for ogone)
        acquirer = self.pool['payment.acquirer'].browse(cr, uid, values.get('acquirer_id'), context=context)

        # compute fees
        custom_method_name = '%s_compute_fees' % acquirer.provider
        fees = 0.0
        if hasattr(Acquirer, custom_method_name):
            fees = getattr(Acquirer, custom_method_name)(
                cr, uid, acquirer.id, values.get('amount', 0.0), values.get('currency_id'), values.get('country_id'), context=None)
        elif acquirer.fees_active:
            fees = self.get_default_fees(acquirer, values.get('amount', 0.0), values.get('country_id'))
        values['fees'] = float_round(fees, 2)

        # custom create
        custom_method_name = '%s_create' % acquirer.provider
        if hasattr(self, custom_method_name):
            values.update(getattr(self, custom_method_name)(cr, uid, values, context=context))

        if values.get('reference', '/') == '/' and acquirer.sequence_id:
            values['reference'] = acquirer.sequence_id.next_by_id()

        return super(PaymentTransaction, self).create(cr, uid, values, context=context)

    def get_default_fees(self, acquirer, amount, country_id):
        if not acquirer.fees_active:
            return 0.0
        fees = acquirer.fees_dom_fixed + acquirer.fees_dom_var / 100.0 * amount
        if country_id and country_id <> acquirer.company_id.country_id.id:
            fees += acquirer.fees_int_fixed + acquirer.fees_int_var / 100.0 * amount
        return fees

    @api.cr_uid_ids_context
    def write(self, cr, uid, ids, values, context=None):
        Acquirer = self.pool['payment.acquirer']
        if ('acquirer_id' in values or 'amount' in values) and 'fees' not in values:
            # The acquirer or the amount has changed, and the fees are not explicitely forced. Fees must be recomputed.
            if isinstance(ids, (int, long)):
                ids = [ids]
            for txn_id in ids:
                vals = dict(values)
                vals['fees'] = 0.0
                transaction = self.browse(cr, uid, txn_id, context=context)
                if 'acquirer_id' in values:
                    acquirer = Acquirer.browse(cr, uid, values['acquirer_id'], context=context) if values['acquirer_id'] else None
                else:
                    acquirer = transaction.acquirer_id
                if acquirer:
                    custom_method_name = '%s_compute_fees' % acquirer.provider
                    amount = (values['amount'] if 'amount' in values else transaction.amount) or 0.0
                    currency_id = values.get('currency_id') or transaction.currency_id.id
                    country_id = values.get('partner_country_id') or transaction.partner_country_id.id
                    fees = 0.0
                    if hasattr(Acquirer, custom_method_name):
                        fees = getattr(Acquirer, custom_method_name)(cr, uid, acquirer.id, amount, currency_id, country_id, context=None)
                    elif acquirer.fees_active:
                        fees = self.get_default_fees(acquirer, amount, country_id)
                    vals['fees'] = float_round(fees, 2)
                res = super(PaymentTransaction, self).write(cr, uid, txn_id, vals, context=context)
            return res
        return super(PaymentTransaction, self).write(cr, uid, ids, values, context=context)

    @api.onchange('acquirer_id')
    def on_change_acquirer_id(self):
        if self.acquirer_id:
            self.medium_id = self.acquirer_id.medium_id.id

    @api.onchange('invoice_ids')
    def on_change_invoice_ids(self):
        self.amount = sum([i.residual or i.amount_total for i in self.invoice_ids])

    @api.onchange('amount', 'acquirer_id', 'partner_country_id')
    def on_change_amount(self):
        self.fees = self.get_default_fees(self.acquirer_id, self.amount, self.partner_country_id.id)

    @api.onchange('partner_id')
    def on_change_partner_id(self):
        partner = None
        if self.partner_id:
            partner = self.partner_id
        self.partner_name = partner and partner.name or False
        self.partner_lang = partner and partner.lang or False
        self.partner_email = partner and partner.email or False
        self.partner_zip = partner and partner.zip or False
        self.partner_address = _partner_format_address(partner and partner.street or '', partner and partner.street2 or '')
        self.partner_city = partner and partner.city or False
        self.partner_country_id = partner and partner.country_id.id or False
        self.partner_phone = partner and partner.phone or False

    def get_next_reference(self, cr, uid, reference, context=None):
        ref_suffix = 1
        init_ref = reference
        while self.pool['payment.transaction'].search_count(cr, SUPERUSER_ID, [('reference', '=', reference)], context=context):
            reference = init_ref + '-' + str(ref_suffix)
            ref_suffix += 1
        return reference

    # --------------------------------------------------
    # FORM RELATED METHODS
    # --------------------------------------------------

    def form_feedback(self, cr, uid, data, acquirer_name, context=None):
        invalid_parameters, tx = None, None

        tx_find_method_name = '_%s_form_get_tx_from_data' % acquirer_name
        if hasattr(self, tx_find_method_name):
            tx = getattr(self, tx_find_method_name)(cr, uid, data, context=context)

        invalid_param_method_name = '_%s_form_get_invalid_parameters' % acquirer_name
        if hasattr(self, invalid_param_method_name):
            invalid_parameters = getattr(self, invalid_param_method_name)(cr, uid, tx, data, context=context)

        if invalid_parameters:
            _error_message = '%s: incorrect tx data:\n' % (acquirer_name)
            for item in invalid_parameters:
                _error_message += '\t%s: received %s instead of %s\n' % (item[0], item[1], item[2])
            _logger.error(_error_message)
            return False

        feedback_method_name = '_%s_form_validate' % acquirer_name
        if hasattr(self, feedback_method_name):
            return getattr(self, feedback_method_name)(cr, uid, tx, data, context=context)

        return True

    # --------------------------------------------------
    # SERVER2SERVER RELATED METHODS
    # --------------------------------------------------

    def s2s_create(self, cr, uid, values, cc_values, context=None):
        tx_id, tx_result = self.s2s_send(cr, uid, values, cc_values, context=context)
        self.s2s_feedback(cr, uid, tx_id, tx_result, context=context)
        return tx_id

    def s2s_send(self, cr, uid, values, cc_values, context=None):
        """ Create and send server-to-server transaction.

        :param dict values: transaction values
        :param dict cc_values: credit card values that are not stored into the
                               payment.transaction object. Acquirers should
                               handle receiving void or incorrect cc values.
                               Should contain :

                                - holder_name
                                - number
                                - cvc
                                - expiry_date
                                - brand
                                - expiry_date_yy
                                - expiry_date_mm
        """
        tx_id, result = None, None

        if values.get('acquirer_id'):
            acquirer = self.pool['payment.acquirer'].browse(cr, uid, values.get('acquirer_id'), context=context)
            custom_method_name = '_%s_s2s_send' % acquirer.provider
            if hasattr(self, custom_method_name):
                tx_id, result = getattr(self, custom_method_name)(cr, uid, values, cc_values, context=context)

        if tx_id is None and result is None:
            tx_id = super(PaymentTransaction, self).create(cr, uid, values, context=context)
        return (tx_id, result)

    def s2s_feedback(self, cr, uid, tx_id, data, context=None):
        """ Handle the feedback of a server-to-server transaction. """
        tx = self.browse(cr, uid, tx_id, context=context)
        invalid_parameters = None

        invalid_param_method_name = '_%s_s2s_get_invalid_parameters' % tx.acquirer_id.provider
        if hasattr(self, invalid_param_method_name):
            invalid_parameters = getattr(self, invalid_param_method_name)(cr, uid, tx, data, context=context)

        if invalid_parameters:
            _error_message = '%s: incorrect tx data:\n' % (tx.acquirer_id.name)
            for item in invalid_parameters:
                _error_message += '\t%s: received %s instead of %s\n' % (item[0], item[1], item[2])
            _logger.error(_error_message)
            return False

        feedback_method_name = '_%s_s2s_validate' % tx.acquirer_id.provider
        if hasattr(self, feedback_method_name):
            return getattr(self, feedback_method_name)(cr, uid, tx, data, context=context)

        return True

    def s2s_get_tx_status(self, cr, uid, tx_id, context=None):
        """ Get the tx status. """
        tx = self.browse(cr, uid, tx_id, context=context)

        invalid_param_method_name = '_%s_s2s_get_tx_status' % tx.acquirer_id.provider
        if hasattr(self, invalid_param_method_name):
            return getattr(self, invalid_param_method_name)(cr, uid, tx, context=context)

        return True

    @api.multi
    def action_draft(self):
        return self.write({'state': 'draft'})

    @api.multi
    def action_pending(self):
        return self.write({'state': 'pending'})

    def _get_statement_line(self, transaction):
        return {'statement_id': transaction.bank_statement_id.id,
                'date': transaction.date_validate or transaction.date_create,
                'name': transaction.reference,
                'ref': "%s%s" % (transaction.acquirer_reference or '',
                                 transaction.partner_reference and " - %s" % transaction.partner_reference or ''),
                'partner_id': transaction.partner_id.id,
                'amount': transaction.amount}

    def _get_fees_line(self, transaction):
        return {'statement_id': transaction.bank_statement_id.id,
                 'date': transaction.date_validate or transaction.date_create,
                 'name': _('Fees %s') % transaction.reference,
                 'ref': "%s%s"%(transaction.acquirer_reference or '',
                                transaction.partner_reference and " - %s"%transaction.partner_reference or ''),
                 'partner_id': transaction.partner_id,
                 'amount': transaction.fees * -1.0}

    @api.multi
    def action_done(self):
        statement_obj = self.env['account.bank.statement.line']
        for transaction in self:
            if transaction.statement_ids:
                continue
            line_dicts = []
            diff = transaction.amount
            for invoice in transaction.invoice_ids:
                if invoice.state not in ['draft', 'proforma', 'proforma2', 'open']:
                    raise ValidationError("The invoice %s must be in draft, proforma or open state"%(invoice.name or invoice.id))
                if invoice.state in ['draft','proforma','proforma2']:
                    invoice.signal_workflow('invoice_open')
                diff -= invoice.residual
                if float_round(diff,2) < 0.0:
                    if transaction.reconcile == 'total':
                        amount = invoice.residual
                    else:
                        amount = invoice.residual + diff
                else:
                    amount = invoice.residual
                if float_round(amount,2) > 0.0:
                    line_dicts.append({'credit': amount,
                                       'name': invoice.name or invoice.internal_number,
                                       'counterpart_move_line_id': [l.id for l in invoice.move_id.line_id if l.account_id.id == invoice.account_id.id][0]})
            if transaction.bank_statement_id:
                lines = []
                line = statement_obj.create(self._get_statement_line(transaction))
                if float_round(diff, 2) > 0.0:
                    line_dicts.append({'credit': diff,
                                       'account_id': transaction.bank_statement_id.journal_id.profit_account_id.id,
                                       'name': _('Adjust of %s')%transaction.reference})
                elif float_round(diff, 2) < 0.0 and transaction.reconcile == 'total':
                    line_dicts.append({'debit': diff * -1.0,
                                       'account_id': transaction.bank_statement_id.journal_id.loss_account_id.id,
                                       'name': _('Adjust of %s') % transaction.reference})
                line.process_reconciliation(line_dicts)
                lines.append(line)
                if transaction.acquirer_id.fees_active:
                    statement_dicts = []
                    statement_dict = self._get_fees_line(transaction)
                    if statement_dict.get('account_id'):
                        statement_dicts = [{'debit': transaction.fees,
                                       'account_id': statement_dict.get('account_id'),
                                       'name': _('Fees %s') % transaction.reference}]
                        del statement_dict['account_id']
                    line = statement_obj.create(statement_dict)
                    if statement_dicts:
                        line.process_reconciliation(statement_dicts)
                    lines.append(line)
                transaction.statement_ids = [l.id for l in lines]
        return self.write({'state': 'done'})

    @api.multi
    def action_error(self):
        return self.write({'state': 'error'})

    @api.multi
    def action_cancel(self):
        for transaction in self:
            transaction.statement_ids.cancel()
            transaction.statement_ids.unlink()
        return self.write({'state': 'cancel'})