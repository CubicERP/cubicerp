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

import logging
import time

from openerp.osv import fields, osv
from openerp.tools.translate import _

_logger = logging.getLogger(__name__)


class payment_order(osv.osv):
    _name = 'payment.order'
    _description = 'Payment Order'
    _inherit = ['mail.thread']
    _order = 'name desc'

    #dead code
    def get_wizard(self, type):
        _logger.warning("No wizard found for the payment type '%s'.", type)
        return None

    def _total(self, cursor, user, ids, name, args, context=None):
        if not ids:
            return {}
        res = {}
        for order in self.browse(cursor, user, ids, context=context):
            if order.line_ids:
                res[order.id] = reduce(lambda x, y: x + y.amount, order.line_ids, 0.0)
            else:
                res[order.id] = 0.0
        return res

    _columns = {
        'date_scheduled': fields.date('Scheduled Date', required=True, states={'done':[('readonly', True)]},
                                      help='Select a date if you have chosen Preferred Date to be fixed.'),
        'name': fields.char('Number', required=1, states={'done': [('readonly', True)]}, copy=False),
        'type': fields.selection([('request','Funds Request'),
                                  ('payment','Payment Order')], 'Type', required=True, states={'done': [('readonly', True)]}),
        'reference': fields.char('Reference', states={'done': [('readonly', True)]}),
        'mode': fields.many2one('payment.mode', 'Payment Mode', select=True, required=1, states={'done': [('readonly', True)]}, help='Select the Payment Mode to be applied.'),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('cancel', 'Cancelled'),
            ('open', 'Confirmed'),
            ('approve', 'Approved'),
            ('done', 'Done')], 'Status', select=True, copy=False, track_visibility='onchange',
            help='When an order is placed the status is \'Draft\'.\n Once the bank is confirmed the status is set to \'Confirmed\'.\n Then the order is paid the status is \'Done\'.'),
        'line_ids': fields.one2many('payment.line', 'order_id', 'Payment lines', states={'done': [('readonly', True)]}),
        'total': fields.function(_total, string="Total", type='float'),
        'user_id': fields.many2one('res.users', 'Responsible', required=True, states={'done': [('readonly', True)]}),
        'approve_user_id': fields.many2one('res.users', 'Approve User', readonly=True),
        'done_user_id': fields.many2one('res.users', 'Done User', readonly=True),
        'date_prefered': fields.selection([
            ('now', 'Directly'),
            ('due', 'Due date'),
            ('fixed', 'Fixed date')
            ], "Preferred Date", change_default=True, required=True, states={'done': [('readonly', True)]}, help="Choose an option for the Payment Order:'Fixed' stands for a date specified by you.'Directly' stands for the direct execution.'Due date' stands for the scheduled date of execution."),
        'date_created': fields.datetime('Creation Date', readonly=True),
        'date_approve': fields.datetime('Approve Date', readonly=True),
        'date_done': fields.datetime('Execution Date', readonly=True),
        'company_id': fields.related('mode', 'company_id', type='many2one', relation='res.company', string='Company', store=True, readonly=True),
        'period_id': fields.many2one('account.period', 'Force Period', states={'done': [('readonly', True)]}),
        'move_id': fields.many2one('account.move', 'Account Move', readonly=True),
    }

    _defaults = {
        'user_id': lambda self,cr,uid,context: uid,
        'state': 'draft',
        'date_prefered': 'due',
        'date_scheduled': lambda *a: time.strftime('%Y-%m-%d'),
        'date_created': fields.datetime.now,
        'name': '/',
        'type': 'request',
    }

    def create(self, cr, uid, vals, context=None):
        if vals.get('name', '/') == '/':
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'payment.order')
        return super(payment_order, self).create(cr, uid, vals, context=context)

    def set_to_draft(self, cr, uid, ids, *args):
        self.write(cr, uid, ids, {'state': 'draft'})
        self.create_workflow(cr, uid, ids)
        return True

    def action_open(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'date_created': fields.datetime.now()})

    def action_approve(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'approve_user_id': uid, 'date_approve': fields.datetime.now()}, context=context)

    def action_cancel(self, cr, uid, ids, context=None):
        move_pool = self.pool.get('account.move')
        move_ids = []
        move_to_cancel = []
        for order in self.browse(cr, uid, ids, context=context):
            if order.move_id:
                move_ids.append(order.move_id.id)
                if order.move_id.state == 'posted':
                    move_to_cancel.append(order.move_id.id)
        move_pool.button_cancel(cr, uid, move_to_cancel, context=context)
        move_pool.unlink(cr, uid, move_ids, context=context)
        return self.write(cr, uid, ids, {'state': 'cancel'}, context=context)

    def set_done(self, cr, uid, ids, context=None):
        line_obj = self.pool.get('account.move.line')
        move_obj = self.pool.get('account.move')
        for order in self.browse(cr, uid, ids, context=context):
            if order.type != 'payment':
                continue
            if not order.period_id:
                period_id = self.pool.get('account.period').find(cr, uid, order.date_scheduled, context=context)[0]
            else:
                period_id = order.period_id.id
            move_id = move_obj.create(cr, uid, {'journal_id': order.mode.journal.id,
                                                                     'date': order.date_scheduled,
                                                                     'period_id': period_id,
                                                                     'ref': order.name}, context=context)
            lines = {}
            balance = {}
            for line in order.line_ids:
                if not line.move_line_id:
                    raise osv.except_osv(_('Data Error!'), _(
                        'The line "%s" has not properly filled account move line!') % (line.name))
                key = (line.move_line_id.partner_id.id,line.move_line_id.account_id.id)
                lines[key] = lines.get(key, []) + [line.move_line_id.id]
                balance[key] = balance.get(key, 0.0) + line.move_line_id.debit - line.move_line_id.credit
            reconcile = []
            amt = 0.0
            for key in lines:
                amt += balance[key]
                line_id = line_obj.create(cr, uid, {'move_id': move_id,
                                          'partner_id': key[0],
                                          'account_id': key[1],
                                          'name': order.name,
                                          'ref': order.reference,
                                          'date': order.date_scheduled,
                                          'journal_id': order.mode.journal.id,
                                          'period_id': period_id,
                                          'analytic_account_id': order.mode.analytic_id and order.mode.analytic_id.id or False,
                                          'debit': balance[key] < 0.0 and -balance[key] or 0.0,
                                          'credit': balance[key] > 0.0 and balance[key] or 0.0}, context=context)
                reconcile += [lines[key] + [line_id]]
            line_obj.create(cr, uid, {'move_id': move_id,
                                      'account_id': order.mode.account_id.id,
                                      'partner_id': False,
                                      'name': order.name,
                                      'ref': order.reference,
                                      'date': order.date_scheduled,
                                      'journal_id': order.mode.journal.id,
                                      'period_id': period_id,
                                      'analytic_account_id': order.mode.analytic_id and order.mode.analytic_id.id or False,
                                      'debit': amt > 0.0 and amt or 0.0,
                                      'credit': amt < 0.0 and -amt or 0.0}, context=context)
            self.write(cr, uid, [order.id], {'move_id': move_id}, context=context)
            if order.mode.journal.entry_posted:
                move_obj.post(cr, uid, [move_id], context=context)
            for rec_ids in reconcile:
                line_obj.reconcile_partial(cr, uid, rec_ids, context=context)
        return self.write(cr, uid, ids, {'date_done': fields.datetime.now(),
                                         'done_user_id': uid,
                                         'state': 'done'})

    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        payment_line_obj = self.pool.get('payment.line')
        payment_line_ids = []

        if (vals.get('date_prefered', False) == 'fixed' and not vals.get('date_scheduled', False)) or vals.get('date_scheduled', False):
            for order in self.browse(cr, uid, ids, context=context):
                for line in order.line_ids:
                    payment_line_ids.append(line.id)
            payment_line_obj.write(cr, uid, payment_line_ids, {'date': vals.get('date_scheduled', False)}, context=context)
        elif vals.get('date_prefered', False) == 'due':
            vals.update({'date_scheduled': False})
            for order in self.browse(cr, uid, ids, context=context):
                for line in order.line_ids:
                    payment_line_obj.write(cr, uid, [line.id], {'date': line.ml_maturity_date}, context=context)
        elif vals.get('date_prefered', False) == 'now':
            vals.update({'date_scheduled': False})
            for order in self.browse(cr, uid, ids, context=context):
                for line in order.line_ids:
                    payment_line_ids.append(line.id)
            payment_line_obj.write(cr, uid, payment_line_ids, {'date': False}, context=context)
        return super(payment_order, self).write(cr, uid, ids, vals, context=context)


class payment_line(osv.osv):
    _name = 'payment.line'
    _description = 'Payment Line'

    def translate(self, orig):
        return {
                "due_date": "date_maturity",
                "reference": "ref"}.get(orig, orig)

    def _info_owner(self, cr, uid, ids, name=None, args=None, context=None):
        result = {}
        for line in self.browse(cr, uid, ids, context=context):
            owner = line.order_id.mode.bank_id.partner_id
            result[line.id] = self._get_info_partner(cr, uid, owner, context=context)
        return result

    def _get_info_partner(self,cr, uid, partner_record, context=None):
        if not partner_record:
            return False
        st = partner_record.street or ''
        st1 = partner_record.street2 or ''
        zip = partner_record.zip or ''
        city = partner_record.city or  ''
        zip_city = zip + ' ' + city
        cntry = partner_record.country_id and partner_record.country_id.name or ''
        return partner_record.name + "\n" + st + " " + st1 + "\n" + zip_city + "\n" +cntry

    def _info_partner(self, cr, uid, ids, name=None, args=None, context=None):
        result = {}
        for line in self.browse(cr, uid, ids, context=context):
            result[line.id] = False
            if not line.partner_id:
                break
            result[line.id] = self._get_info_partner(cr, uid, line.partner_id, context=context)
        return result

    #dead code
    def select_by_name(self, cr, uid, ids, name, args, context=None):
        if not ids: return {}
        partner_obj = self.pool.get('res.partner')

        cr.execute("""SELECT pl.id, ml.%s
            FROM account_move_line ml
                INNER JOIN payment_line pl
                ON (ml.id = pl.move_line_id)
                WHERE pl.id IN %%s"""% self.translate(name),
                   (tuple(ids),))
        res = dict(cr.fetchall())

        if name == 'partner_id':
            partner_name = {}
            for p_id, p_name in partner_obj.name_get(cr, uid,
                filter(lambda x:x and x != 0,res.values()), context=context):
                partner_name[p_id] = p_name

            for id in ids:
                if id in res and partner_name:
                    res[id] = (res[id],partner_name[res[id]])
                else:
                    res[id] = (False,False)
        else:
            for id in ids:
                res.setdefault(id, (False, ""))
        return res

    def _amount(self, cursor, user, ids, name, args, context=None):
        if not ids:
            return {}
        currency_obj = self.pool.get('res.currency')
        if context is None:
            context = {}
        res = {}

        for line in self.browse(cursor, user, ids, context=context):
            ctx = context.copy()
            ctx['date'] = line.order_id.date_done or time.strftime('%Y-%m-%d')
            res[line.id] = currency_obj.compute(cursor, user, line.currency.id,
                    line.company_currency.id,
                    line.amount_currency, context=ctx)
        return res

    def _get_currency(self, cr, uid, context=None):
        user_obj = self.pool.get('res.users')
        currency_obj = self.pool.get('res.currency')
        user = user_obj.browse(cr, uid, uid, context=context)

        if user.company_id:
            return user.company_id.currency_id.id
        else:
            return currency_obj.search(cr, uid, [('rate', '=', 1.0)])[0]

    def _get_date(self, cr, uid, context=None):
        if context is None:
            context = {}
        payment_order_obj = self.pool.get('payment.order')
        date = False

        if context.get('order_id') and context['order_id']:
            order = payment_order_obj.browse(cr, uid, context['order_id'], context=context)
            if order.date_prefered == 'fixed':
                date = order.date_scheduled
            else:
                date = time.strftime('%Y-%m-%d')
        return date

    def _get_reference(self, cr, uid, line, context=None):
        res = False
        if line.move_line_id:
            if line.move_line_id.invoice:
                res = line.move_line_id.invoice.supplier_invoice_number or line.move_line_id.invoice.reference
            else:
                res = line.move_line_id.ref or line.move_line_id.name
        return res

    def _get_ml_inv_ref(self, cr, uid, ids, args, fields, context=None):
        res = {}
        for line in self.browse(cr, uid, ids):
            res[line.id] = self._get_reference(cr, uid, line, context=context)
        return res

    def _get_ml_maturity_date(self, cr, uid, ids, *a):
        res = {}
        for id in self.browse(cr, uid, ids):
            if id.move_line_id:
                res[id.id] = id.move_line_id.date_maturity
            else:
                res[id.id] = False
        return res

    def _get_ml_created_date(self, cr, uid, ids, *a):
        res = {}
        for id in self.browse(cr, uid, ids):
            if id.move_line_id:
                res[id.id] = id.move_line_id.date_created
            else:
                res[id.id] = False
        return res

    _columns = {
        'name': fields.char('Your Reference', required=True),
        'communication': fields.char('Communication', required=True, help="Used as the message between ordering customer and current company. Depicts 'What do you want to say to the recipient about this order ?'"),
        'communication2': fields.char('Communication 2', help='The successor message of Communication.'),
        'move_line_id': fields.many2one('account.move.line', 'Entry line', domain=[('reconcile_id', '=', False), ('account_id.type', '=', 'payable')], help='This Entry Line will be referred for the information of the ordering customer.'),
        'amount_currency': fields.float('Amount in Partner Currency', digits=(16, 2),
            required=True, help='Payment amount in the partner currency'),
        'currency': fields.many2one('res.currency','Partner Currency', required=True),
        'company_currency': fields.many2one('res.currency', 'Company Currency', readonly=True),
        'bank_id': fields.many2one('res.partner.bank', 'Destination Bank Account'),
        'order_id': fields.many2one('payment.order', 'Order', required=True,
            ondelete='cascade', select=True),
        'partner_id': fields.many2one('res.partner', string="Partner", help='The Ordering Customer'),
        'amount': fields.function(_amount, string='Amount in Company Currency',
            type='float',
            help='Payment amount in the company currency'),
        'ml_date_created': fields.function(_get_ml_created_date, string="Effective Date", type='date', help="Invoice Effective Date"),
        'ml_maturity_date': fields.function(_get_ml_maturity_date, type='date', string='Due Date'),
        'ml_inv_ref': fields.function(_get_ml_inv_ref, type='char', string='Invoice Ref.'),
        'info_owner': fields.function(_info_owner, string="Owner Account", type="text", help='Address of the Main Partner'),
        'info_partner': fields.function(_info_partner, string="Destination Account", type="text", help='Address of the Ordering Customer.'),
        'date': fields.date('Payment Date', help="If no payment date is specified, the bank will treat this payment line directly"),
        'create_date': fields.datetime('Created', readonly=True),
        'state': fields.selection([('normal','Free'), ('structured','Structured')], 'Communication Type', required=True),
        'bank_statement_line_id': fields.many2one('account.bank.statement.line', 'Bank statement line'),
        'company_id': fields.related('order_id', 'company_id', type='many2one', relation='res.company', string='Company', store=True, readonly=True),
        'mode': fields.related('order_id', 'mode', type='many2one', relation='payment.mode', string='Payment Mode', store=True, readonly=True),
        'order_state': fields.related('order_id', 'state', type='char', string='Order State', store=True, readonly=True),
        'user_id': fields.related('order_id', 'user_id', type='many2one', relation='res.users', string='Responsible', store=True, readonly=True),
    }
    _defaults = {
        'name': lambda obj, cursor, user, context: obj.pool.get('ir.sequence'
            ).get(cursor, user, 'payment.line'),
        'state': 'structured',
        'currency': _get_currency,
        'company_currency': _get_currency,
        'date': _get_date,
    }
    _sql_constraints = [
        ('name_uniq', 'UNIQUE(order_id,name)', 'The payment line name must be unique!'),
    ]

    def onchange_move_line(self, cr, uid, ids, move_line_id, payment_type, date_prefered, date_scheduled, currency=False, company_currency=False, context=None):
        data = {}
        move_line_obj = self.pool.get('account.move.line')

        data['amount_currency'] = data['communication'] = data['partner_id'] = data['bank_id'] = data['amount'] = False

        if move_line_id:
            line = move_line_obj.browse(cr, uid, move_line_id, context=context)
            data['amount_currency'] = line.amount_residual_currency

            res = self.onchange_amount(cr, uid, ids, data['amount_currency'], currency,
                                       company_currency, context)
            if res:
                data['amount'] = res['value']['amount']
            data['partner_id'] = line.partner_id.id
            temp = line.currency_id and line.currency_id.id or False
            if not temp:
                if line.invoice:
                    data['currency'] = line.invoice.currency_id.id
            else:
                data['currency'] = temp

            # calling onchange of partner and updating data dictionary
            temp_dict = self.onchange_partner(cr, uid, ids, line.partner_id.id, payment_type)
            data.update(temp_dict['value'])

            data['communication'] = line.ref

            if date_prefered == 'now':
                #no payment date => immediate payment
                data['date'] = False
            elif date_prefered == 'due':
                data['date'] = line.date_maturity
            elif date_prefered == 'fixed':
                data['date'] = date_scheduled
        return {'value': data}

    def onchange_amount(self, cr, uid, ids, amount, currency, cmpny_currency, context=None):
        if (not amount) or (not cmpny_currency):
            return {'value': {'amount': False}}
        res = {}
        currency_obj = self.pool.get('res.currency')
        company_amount = currency_obj.compute(cr, uid, currency, cmpny_currency, amount)
        res['amount'] = company_amount
        return {'value': res}

    def onchange_partner(self, cr, uid, ids, partner_id, payment_type, context=None):
        data = {}
        partner_obj = self.pool.get('res.partner')
        payment_mode_obj = self.pool.get('payment.mode')
        data['info_partner'] = data['bank_id'] = False

        if partner_id:
            part_obj = partner_obj.browse(cr, uid, partner_id, context=context)
            partner = part_obj.name or ''
            data['info_partner'] = self._get_info_partner(cr, uid, part_obj, context=context)

            if part_obj.bank_ids and payment_type:
                bank_type = payment_mode_obj.suitable_bank_types(cr, uid, payment_type, context=context)
                for bank in part_obj.bank_ids:
                    if bank.state in bank_type:
                        data['bank_id'] = bank.id
                        break
        return {'value': data}

    def fields_get(self, cr, uid, fields=None, context=None, write_access=True, attributes=None):
        res = super(payment_line, self).fields_get(cr, uid, fields, context, write_access, attributes)
        if 'communication2' in res:
            res['communication2'].setdefault('states', {})
            res['communication2']['states']['structured'] = [('readonly', True)]
            res['communication2']['states']['normal'] = [('readonly', False)]
        return res


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
