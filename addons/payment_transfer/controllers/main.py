# -*- coding: utf-8 -*-
import logging
import pprint
import werkzeug

from odoo import http, exceptions
from odoo.http import request

_logger = logging.getLogger(__name__)


class OgoneController(http.Controller):
    _accept_url = '/payment/transfer/feedback'

    @http.route([
        '/payment/transfer/feedback',
    ], type='http', auth='none', csrf=False)
    def transfer_form_feedback(self, **post):
        _logger.info('Beginning form_feedback with post data %s', pprint.pformat(post))  # debug
        request.env['payment.transaction'].sudo().form_feedback(post, 'transfer')
        return werkzeug.utils.redirect(post.pop('return_url', '/'))

    @http.route(['/payment/transfer/s2s'], type='json', auth='public', csrf=False)
    def transfer_form_s2s(self, **kwargs):

        # find or create transaction
        tx_type = 'form'
        tx = request.env['payment.transaction'].sudo()
        acquirer = request.env['payment.acquirer'].browse(int(kwargs['acquirer_id']))
        payment_token = None
        order = request.env['sale.order'].sudo().browse(request.session.sale_order_id)
        tx = tx._check_or_create_sale_tx(order, acquirer, payment_token=payment_token, tx_type=tx_type)
        request.session['sale_transaction_id'] = tx.id

        request.env['payment.transaction'].sudo().form_feedback(kwargs, 'transfer')

        try:
            if not kwargs.get('partner_id'):
                kwargs = dict(kwargs, partner_id=request.env.user.partner_id.id)
            token = acquirer.s2s_process(kwargs)
            tx.write({'acquirer_reference': kwargs.get('op_number'),'payment_token_id':token.id})
        except exceptions.ValidationError as e:
            message = e.args[0]
            if isinstance(message, dict) and 'missing_fields' in message:
                msg = _("The transaction cannot be processed because some contact details are missing or invalid: ")
                message = msg + ', '.join(message['missing_fields']) + '. '
                if request.env.user._is_public():
                    message += _("Please sign in to complete your profile.")
                    # update message if portal mode = b2b
                    if request.env['ir.config_parameter'].sudo().get_param('auth_signup.allow_uninvited',
                                                                           'False').lower() == 'false':
                        message += _(
                            "If you don't have any account, please ask your salesperson to update your profile. ")
                else:
                    message += _("Please complete your profile. ")

            return {
                'error': message
            }

        if not token:
            res = {
                'result': False,
            }
            return res

        res = {
            'result': True,
            'id': token.id,
            'short_name': token.short_name,
            '3d_secure': False,
            'verified': True,  # Authorize.net does a transaction type of Authorization Only
            # As Authorize.net already verify this card, we do not verify this card again.
        }
        # token.validate() don't work with Authorize.net.
        # Payments made via Authorize.net are settled and allowed to be refunded only on the next day.
        # https://account.authorize.net/help/Miscellaneous/FAQ/Frequently_Asked_Questions.htm#Refund
        # <quote>The original transaction that you wish to refund must have a status of Settled Successfully.
        # You cannot issue refunds against unsettled, voided, declined or errored transactions.</quote>
        # return werkzeug.utils.redirect(kwargs.pop('return_url', '/'))

        return res
