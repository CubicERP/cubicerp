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

from openerp.osv import osv, fields
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round
import time

class account_load(osv.Model):
    
    def _get_period(self, cr, uid, context=None):
        if context is None:
            context = {}
        company_id = context.get('company_id', self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id)
        today = time.strftime('%Y-%m-%d')
        res = self.pool.get('account.period').search(cr, uid, [('fiscalyear_id.date_start','<=',today),('fiscalyear_id.date_stop','>=',today),
                                            ('special', '=', True),
                                            ('company_id', '=', company_id)],
                                                limit=1)
        return res and res[0] or False
    
    def _get_journal(self, cr, uid, context=None):
        if context is None:
            context = {}
        company_id = context.get('company_id', self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id)
        res = self.pool.get('account.journal').search(cr, uid, [('type', '=', 'situation'),
                                            ('company_id', '=', company_id)],
                                                limit=1)
        return res and res[0] or False
    
    def _get_amount_total(self, cr, uid, ids, name, args, context=None):
        res = {}
        for load in self.browse(cr, uid, ids, context=context):
            res[load.id] = 0.0
            for line in load.line_ids:
                res[load.id] += line.amount_load
        return res
    
    _name = "account.load"
    _description = "Account Initial Load"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _columns = {
            'company_id': fields.many2one('res.company', required=True, string='Company', readonly=True, states={'draft':[('readonly',False)]}),
            'name': fields.char('Name',64, required=True, readonly=True, states={'draft':[('readonly',False)]}),
            'ref': fields.char('Reference',256, readonly=True, states={'draft':[('readonly',False)]}),
            'journal_id': fields.many2one('account.journal','Journal', required=True, readonly=True, states={'draft':[('readonly',False)]},
                                          help="This journal is used to obtain the credit/debit account to complete the account entry"),
            'period_id': fields.many2one('account.period','Period', required=True, readonly=True, states={'draft':[('readonly',False)]},
                                         help="All entries will be written on this period"),
            'date': fields.date('Date', required=True, readonly=True, states={'draft':[('readonly',False)]}),
            'origin': fields.char('Origin',64, readonly=True, states={'draft':[('readonly',False)]}),
            'user_id': fields.many2one('res.users', string="User", required=True, readonly=True, states={'draft':[('readonly',False)]}),
            'line_ids': fields.one2many('account.load.move','load_id', string="Load Lines", readonly=True,
                                        states={'draft':[('readonly',False)]}),
            'state': fields.selection([('draft','Draft'),
                                       ('posted','Posted')], string="State", readonly=True),
            'currency_id': fields.related('company_id','currency_id', string="Currency", type="many2one", relation="res.currency"),
            'notes': fields.text('Notes'),
            'amount_total': fields.function(_get_amount_total,string="Amount Total",type="float"),
        }
    _defaults = {
            'name': '/',
            'date': lambda *a: time.strftime('%Y-%m-%d'),
            'state': 'draft',
            'company_id': lambda s,cr,u,c: s.pool.get('res.users').browse(cr,u,u,context=c).company_id.id,
            'user_id': lambda s,cr,u,c: u,
            'period_id': _get_period,
            'journal_id': _get_journal,
        }

    def create(self, cr, uid, vals, context=None):
        context = context or {}
        if vals.has_key('journal_id'):
            journal = self.pool.get('account.journal').browse(cr, uid, vals.get('journal_id'), context=context)
            if not journal.sequence_id:
                raise osv.except_osv(_('Error!'), _('Please define sequence on the journal related to this load.'))
            if not (journal.default_debit_account_id and journal.default_credit_account_id):
                raise osv.except_osv(_('Error!'), _('Please define the credit and debit account on the journal related to this load.'))
            if vals.get('name','/') == '/':    
                vals['name'] = self.pool.get('ir.sequence').get_id(cr, uid, journal.sequence_id.id)
        return super(account_load,self).create(cr, uid, vals, context=context)
    
    def button_cancel(self, cr, uid, ids, context=None):
        load_move_obj = self.pool.get('account.load.move')
        for load in self.browse(cr, uid, ids, context=context):
            for line in load.line_ids:
                if line.state in ('posted'):
                    load_move_obj.button_cancel(cr, uid, [line.id], context=context)
        return self.write(cr, uid, ids, {'state': 'draft'}, context=context)
    
    def button_validate(self, cr, uid, ids, context=None):
        load_move_obj = self.pool.get('account.load.move')
        for load in self.browse(cr, uid, ids, context=context):
            for line in load.line_ids:
                if line.state in ('draft'):
                    load_move_obj.button_validate(cr, uid, [line.id], context=context)
        return self.write(cr, uid, ids, {'state': 'posted'}, context=context)

class account_load_move(osv.Model):

    def _to_move_ids(self, cr, uid, ids, context=None):
        res = {}
        for load_move in self.browse(cr, uid, [x for x in ids if x != None], context=context):
            res[load_move.move_id.id] = True
        return res.keys()
    
    def _to_move_id(self, cr, uid, id, context=None):
        return self.browse(cr, uid, id, context=context).move_id.id
    
    def _get_one_line(self, cr, uid, ids, name, args, context=None):
        res = {}
        i=0
        for load_move in self.browse(cr, uid, ids, context=context):
            res[load_move.id] = {
                    'account_id': False,
                    'partner_id': False,
                    'amount_load': 0.0,
                    'quantity': 0.0,
                    'date_maturity': False,
                    'currency_id': False,
                    'currency_amount': 0.0,
                }
            line_selected = False
            date_maturity = ''
            cr.execute("select j.default_debit_account_id, j.default_credit_account_id, jm.type from account_journal j, account_load l, account_load_move lm, account_move am, account_journal jm where l.journal_id=j.id and l.id = lm.load_id and lm.move_id = am.id and am.journal_id = jm.id and lm.id=%s"%ids[i])
            acc_list = cr.fetchall()[0]
            journal_type = acc_list[2]
            acc_list = acc_list[:2]
            for line in load_move.line_id:
                if line.account_id.id in acc_list:
                    continue
                if line.date_maturity:
                    if date_maturity <= line.date_maturity:
                        line_selected = line
                elif not line_selected:
                    line_selected = line
                res[load_move.id]['currency_amount'] += line.amount_currency
                res[load_move.id]['quantity'] += line.quantity
                res[load_move.id]['amount_load'] += (line.debit - line.credit) * (journal_type in ('purchase','purchase_refund') and -1 or 1)
            if line_selected:
                res[load_move.id].update(self._one_line_field_read(cr, uid, ids, line_selected, context=context))
            i += 1
        return res
    
    def _one_line_field_read(self, cr, uid, ids, line, context=None):
        return {
                'account_id': line.account_id.id,
                'partner_id': line.partner_id.id,
                'analytic_account_id': line.analytic_account_id.id,
                'asset_id': line.asset_id.id,
                'product_id': line.product_id.id,
                'date_maturity': line.date_maturity,
                'currency_id': line.currency_id.id,
            }
        
    def _one_line_field_map(self, cr, uid, id, context=None):
        return {
                'account_id': 'account_id',
                'partner_id': 'partner_id',
                'analytic_account_id': 'analytic_account_id',
                'asset_id': 'asset_id',
                'product_id': 'product_id',
                'quantity': 'quantity',
                'date_maturity': 'date_maturity',
                'currency_id': 'currency_id',
                'currency_amount': 'amount_currency',
                'amount_load': context.get('amount_load','debit'),
            }
    
    def _one_line_default_values(self, cr, uid, id, context=None):
        cr.execute('select lm.move_id,l.period_id,m.name,l.date,l.state from account_load l, account_load_move lm, account_move m where l.id=lm.load_id and lm.move_id=m.id and lm.id=%s'%id)
        f = cr.fetchall()[0]
        return {
                'move_id': f[0],
                'period_id': f[1],
                'name': f[2],
                'date': f[3],
                'partner_id': False,
                'state': f[4], 
            }
    
    def _one_line_values(self, cr, uid, load_move, values, vals, context=None):
        if context is None: context = {}
        if not values: values = {}
        context_map = context.copy()
        if vals.has_key('amount_load'):
            values['debit'] = 0.0
            values['credit'] = 0.0
            if load_move.journal_id.type in ('purchase','purchase_refund'):
                vals['amount_load'] *= -1 
            if vals.get('amount_load', 0.0) < 0.0:
                context_map['amount_load'] = 'credit'
                vals['amount_load'] = abs(vals['amount_load'])
                vals['amount_currency'] = abs(load_move.currency_amount) * -1
            else:
                vals['amount_currency'] = abs(load_move.currency_amount)
        if vals.has_key('product_id'):
            values['quantity'] = load_move.quantity
        if vals.has_key('currency_id'):
            if not vals.get('currency_id'):
                values['amount_currency'] = 0.0
        field_map = self._one_line_field_map(cr, uid, id, context=context_map)
        for k in vals.keys():
            if field_map.has_key(k):
                values[field_map[k]] = vals[k]
            else:
                values[k] = vals[k]
        return values
        
    def _adjust_counterpart(self, cr, uid, id, acc_list, context=None):
        res = []
        line_obj = self.pool.get("account.move.line")
        cp_unlink = []
        debit = credit = 0.0
        for line in self.browse(cr, uid, id, context=context).line_id:
            if line.account_id.id in acc_list:
                cp_unlink.append(line.id)
            else:
                debit += line.debit
                credit += line.credit
        values = self._one_line_default_values(cr, uid, id, context=context)
        line_obj.unlink(cr, uid, cp_unlink, context=context)
        if debit:
            values['account_id'] = acc_list[1]
            values['debit'] = 0.0
            values['credit'] = debit
            res.append(line_obj.create(cr, uid, values, context=context))
        if credit:
            values['account_id'] = acc_list[0]
            values['debit'] = credit
            values['credit'] = 0.0
            res.append(line_obj.create(cr, uid, values, context=context))
        return res
    
    def _set_one_line(self, cr, uid, id, name, value, arg, context=None):
        if context is None:
            context = {}
        line_obj = self.pool.get("account.move.line")
        load_move = self.browse(cr, uid, id, context=context)
        line_id = False
        date_maturity = ''
        cr.execute("select j.default_debit_account_id, j.default_credit_account_id from account_journal j, account_load l, account_load_move lm where l.journal_id=j.id and l.id = lm.load_id and lm.id=%s"%id)
        acc_list = cr.fetchall()[0]
        for line in load_move.line_id:
            if line.account_id.id in acc_list:
                continue
            if line.date_maturity:
                if date_maturity <= line.date_maturity:
                    line_id = line.id
            elif not line_id:
                line_id = line.id
        field_map = self._one_line_field_map(cr, uid, id, context=context)
        # Define the default dictionary values for the create 
        default_values = self._one_line_default_values(cr, uid, id, context=context)
        values = {}
        if not line_id:
            if default_values.has_key(field_map[name]):
                del default_values[field_map[name]]
            values = default_values.copy() 
        values = self._one_line_values(cr, uid, load_move, values, {name: value}, context=context)
        values['account_id'] = load_move.account_id.id
        if line_id:
            line_obj.write(cr, uid, [line_id], values, context=context)
        else:
            context['journal_id'] = load_move.journal_id.id
            context['period_id'] = load_move.load_id.period_id.id
            if load_move.currency_amount:
                values['amount_currency'] = load_move.currency_amount
            if load_move.quantity:
                values['quantity'] = load_move.quantity
            if load_move.currency_id:
                values['currency_id'] = load_move.currency_id.id
            line_obj.create(cr, uid, values, context=context)
        self._adjust_counterpart(cr, uid, id, acc_list, context=context)
        return True
    
    def _get_load_move_from_move_line(self, cr, uid, ids, context=None):
        res = {}
        load_move_obj = self.pool.get('account.load.move')
        load_move_ids = []
        for move_line in self.pool.get('account.move.line').browse(cr, uid, ids, context=context):
            load_move_ids += load_move_obj.search(cr, uid, [('move_id','=',move_line.move_id.id)], context=context)
        return load_move_ids
    
    _inherits = {'account.move':'move_id'}
    _name = "account.load.move"
    _description = "Account Initial Load Moves"
    _columns = {
            'load_id': fields.many2one('account.load', string="Account Load", ondelete="cascade"),
            'move_id': fields.many2one('account.move', string="Account Move", ondelete="cascade", required=True, select=True),
            'account_id': fields.function(_get_one_line,string="Account",type="many2one",relation="account.account",
                                                  multi="load_all", fnct_inv=_set_one_line, required=False  , readonly=True, states={'draft':[('readonly',False)]},
                                                  store={
                                                        'account.move.line': (_get_load_move_from_move_line, ['account_id'], 20),
                                                    }),
            'account_user_type': fields.related('account_id','user_type',string="Account User Type", type="many2one", relation="account.account.type", readonly=True,
                                                store=True),
            'account_type': fields.related('account_id','type',string="Account Type", type="char", readonly=True,
                                           store=True),
            'partner_id': fields.function(_get_one_line,string="Partner",type="many2one",relation="res.partner",
                                                  multi="load_all", fnct_inv=_set_one_line, readonly=True, states={'draft':[('readonly',False)]},
                                                  store={
                                                        'account.move.line': (_get_load_move_from_move_line, ['partner_id'], 20),
                                                    }),
            'amount_load': fields.function(_get_one_line,string="Amount",type="float", 
                                                  multi="load_all", fnct_inv=_set_one_line, required=True, readonly=True, states={'draft':[('readonly',False)]},
                                                  store={
                                                        'account.move': (lambda s,cr,u,i,c: s.pool.get('account.load.move').search(cr, u, [('move_id','in',i)], context=c), ['journal_id'], 20),
                                                        'account.move.line': (_get_load_move_from_move_line, ['debit','credit'], 20),
                                                    }),
            'analytic_account_id': fields.function(_get_one_line,string="Analytic Account",type="many2one",relation="account.analytic.account", 
                                                  multi="load_all", fnct_inv=_set_one_line, readonly=True, states={'draft':[('readonly',False)]},
                                                  store={
                                                        'account.move.line': (_get_load_move_from_move_line, ['analytic_account_id'], 20),
                                                    }),
            'asset_id': fields.function(_get_one_line, string="Asset", type="many2one",
                                                   relation="account.asset.asset",
                                                   multi="load_all", fnct_inv=_set_one_line, readonly=True,
                                                   states={'draft': [('readonly', False)]},
                                                   store={
                                                       'account.move.line': (
                                                       _get_load_move_from_move_line, ['asset_id'], 20),
                                                   }),
            'product_id': fields.function(_get_one_line, string="Product", type="many2one", relation="product.product",
                                           multi="load_all", fnct_inv=_set_one_line, readonly=True,
                                           states={'draft': [('readonly', False)]},
                                           store={
                                               'account.move.line': (_get_load_move_from_move_line, ['product_id'], 20),
                                           }),
            'quantity': fields.function(_get_one_line, string="Quantity", type="float",
                                               multi="load_all", fnct_inv=_set_one_line, readonly=True,
                                               states={'draft': [('readonly', False)]},
                                               store={
                                                   'account.move.line': (
                                                   _get_load_move_from_move_line, ['quantity'], 20),
                                               }),
            'date_maturity': fields.function(_get_one_line,string="Date Maturity",type="date",
                                                  multi="load_all", fnct_inv=_set_one_line, readonly=True, states={'draft':[('readonly',False)]},
                                                  store={
                                                        'account.move.line': (_get_load_move_from_move_line, ['date_maturity'], 20),
                                                    }),
            'currency_id': fields.function(_get_one_line,string="Currency",type="many2one",relation="res.currency", 
                                                  multi="load_all", fnct_inv=_set_one_line, readonly=True, states={'draft':[('readonly',False)]},
                                                  store={
                                                        'account.move.line': (_get_load_move_from_move_line, ['currency_id'], 20),
                                                    }),
            'currency_amount': fields.function(_get_one_line,string="Currency Amount",type="float", 
                                                  multi="load_all", fnct_inv=_set_one_line, readonly=True, states={'draft':[('readonly',False)]},
                                                  store={
                                                        'account.move.line': (_get_load_move_from_move_line, ['amount_currency'], 20),
                                                    }),
        }
    
    def unlink(self, cr, uid, ids, context=None):
        unlink_ids = []
        unlink_move_ids = []
        ids = self.search(cr, uid, [('id','in',ids)], context=context)
        for load_move in self.browse(cr, uid, ids, context=context):
            move_id = load_move.move_id.id
            if not self.search(cr, uid, [('move_id', '=', move_id), ('id', '!=', load_move.id)], context=context):
                 unlink_move_ids.append(move_id)
            unlink_ids.append(load_move.id)
        self.pool.get('account.move').unlink(cr, uid, unlink_move_ids, context=context)
        return super(account_load_move, self).unlink(cr, uid, unlink_ids, context=context)
    
    def button_cancel(self, cr, uid, ids, context=None):
        return self.pool.get('account.move').button_cancel(cr, uid, self._to_move_ids(cr, uid, ids, context=context))
    
    def button_validate(self, cr, uid, ids, context=None):
        return self.pool.get('account.move').button_validate(cr, uid, self._to_move_ids(cr, uid, ids, context=context))
    
    def onchange_journal(self, cr, uid, ids, journal_id, partner_id, amount_load, context=None):
        res = {'value': {}}
        if isinstance(ids, (int, long)):
            ids = [ids]
        if not journal_id:
            return res
        journal = self.pool.get('account.journal').browse(cr, uid, journal_id, context=context)
        if partner_id:
            partner = self.pool.get('res.partner').browse(cr, uid, partner_id, context=context)
            if journal.type in ('sale','sale_refund'):
                res['value']['account_id'] = partner.property_account_receivable.id
            elif journal.type in ('purchase','purchase_refund'):
                res['value']['account_id'] = partner.property_account_payable.id
            else:
                if amount_load < 0.0:
                    res['value']['account_id'] = journal.default_debit_account_id.id
                else:
                    res['value']['account_id'] = journal.default_credit_account_id.id
        else:
            if amount_load < 0.0:
                res['value']['account_id'] = journal.default_debit_account_id.id
            else:
                res['value']['account_id'] = journal.default_credit_account_id.id
        if journal.type in ('sale_refund','purchase_refund') and amount_load > 0.0:
            res['warning'] = {'title':'Warning!','message':'The amount must be less than zero'}
        elif journal.type in ('sale','purchase') and amount_load < 0.0:
            res['warning'] = {'title':'Warning!','message':'The amount must be greater than zero'}
        return res
    
    def onchange_currency(self, cr, uid, ids, journal_id, date, currency_id, currency_amount, company_id, context=None):
        if context is None:
            context = {}
        res = {'value': {}}
        currency_obj = self.pool.get('res.currency')
        if isinstance(ids, (int, long)):
            ids = [ids]
        if not journal_id:
            return res
        journal = self.pool.get('account.journal').browse(cr, uid, journal_id, context=context)
        company = self.pool.get('res.company').browse(cr, uid, company_id, context=context)
        coeff = 1.0
        if journal.type in ('purchase','purchase_refund'):
            coeff = -1.0
        context_currency = context.copy()
        context_currency['date'] = date
        res['value']['amount_load'] = coeff * currency_obj.compute(cr, uid, currency_id, company.currency_id.id, currency_amount, context=context_currency) 
        return res
