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

from openerp import models, fields, api, exceptions, _


class BudgetMove(models.Model):
    _name = "budget.move"
    _description = "Budget Move Transaction"

    @api.model
    def _get_period(self):
        periods = self.env['budget.period'].find()
        return periods and periods[0] or False

    @api.multi
    @api.depends('line_ids', 'line_ids.available', 'line_ids.committed', 'line_ids.provision', 'line_ids.paid')
    def _compute_amount(self):
        for move in self:
            available = committed = provision = paid = total_amount = 0.0
            for line in move.line_ids:
                available += line.available
                committed += line.committed
                provision += line.provision
                paid += line.paid
                if line.available > 0.0:
                    total_amount += line.available
                if line.committed > 0.0:
                    total_amount += line.committed
                if line.provision > 0.0:
                    total_amount += line.provision
                if line.paid > 0.0:
                    total_amount += line.paid

            move.available = available
            move.committed = committed
            move.provision = provision
            move.paid = paid
            move.total_amount = total_amount

    name = fields.Char("Name", required=True, default="/", states={'draft': [('readonly', False)]}, readonly=True)
    ref = fields.Char("Reference", states={'draft': [('readonly', False)]}, readonly=True)
    date = fields.Date("Date", required=True, default=fields.Date.today, states={'draft': [('readonly', False)]},
                       readonly=True)
    period_id = fields.Many2one('budget.period', string="Period", required=True, default=_get_period,
                                states={'draft': [('readonly', False)]}, readonly=True)
    line_ids = fields.One2many('budget.move.line', 'move_id', string="Lines", states={'draft': [('readonly', False)]},
                               readonly=True)
    move_line_id = fields.Many2one('account.move.line', string="Move Line",
                                   states={'draft': [('readonly', False)]}, readonly=True)
    account_move_id = fields.Many2one('account.move', string="Account Entry", related="move_line_id.move_id",
                                      readonly=True, store=True)
    account_journal_id = fields.Many2one('account.journal', string="Account Journal", readonly=True, store=True,
                                         related="move_line_id.move_id.journal_id")
    purchase_id = fields.Many2one('purchase.order', string="Purchase Order", states={'draft': [('readonly', False)]}, readonly=True)
    state = fields.Selection([('draft', 'Draft'),
                              ('done', 'Done')], string="State", readonly=True, default='draft')
    company_id = fields.Many2one('res.company', 'Company', required=True, readonly=True,
                                 states={'draft': [('readonly', False)]},
                                 default=lambda s: s.env['res.company'].company_default_get('budget.budget'))
    available = fields.Float("Available", compute=_compute_amount)
    committed = fields.Float("Committed", compute=_compute_amount)
    provision = fields.Float("Provision", compute=_compute_amount)
    paid = fields.Float("Paid", compute=_compute_amount)
    total_amount = fields.Float("Total Amount", compute=_compute_amount)

    @api.one
    def unlink(self):
        if self.state == 'done':
            raise exceptions.ValidationError(
                _("The Budget Transaction %s must be in draft state, to be deleted!") % (self.name))
        return super(BudgetMove, self).unlink()

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].get('budget.control.move')
        return super(BudgetMove, self).create(vals)

    @api.one
    def action_draft(self):
        self.state = 'draft'

    @api.one
    def action_done(self):
        for line in self.line_ids:
            if line.state <> 'valid':
                raise exceptions.ValidationError(_("The lines must be in valid state. The line %s (%s) is invalid") % (
                    line.name, line.struct_id.get_name()))
        self.state = 'done'

    def _create_move_values(self, line=None, purchase=None, sale=None):
        res = {
            'ref': line and line.move_id.ref or (purchase and purchase.name or ''),
            'move_line_id': line and line.id or False,
            'purchase_id': purchase and purchase.id or False,
        }
        date = line and line.move_id.date or (purchase and purchase.date_order or False)
        if date:
            res['date'] = date
        if line and line.move_id.period_id.budget_period_id:
            res['period_id'] = line.move_id.period_id.budget_period_id.id
        if not res.get('period_id',False) and purchase and purchase.date_order:
            periods = self.env['budget.period'].find(dt=purchase.date_order)
            res['period_id'] = periods and periods[0].id or False
        return res

    def _create_lines_values(self, move, line=None, purchase=None, sale=None, amount=None, struct_id=None, analytic_id=None):
        res = []
        if amount is None:
            amount = line and (line.debit - line.credit) or (purchase and purchase.amount_total or (sale and sale.amount_total or 0.0))
        if struct_id is None:
            struct_id = line and line.budget_struct_id.id or (purchase and purchase.struct_id.id or (sale and sale.struct_id.id or False))
        if analytic_id is None:
            analytic_ids = line and [{'analytic_id':line.analytic_account_id.id}] or (sale and sale.project_id and [{'analytic_id':sale.project_id.id}] or [])
            if not analytic_ids and purchase:
                total = 0.0
                for po_line in purchase.order_line:
                    if po_line.account_analytic_id.id not in [a['analytic_id'] for a in analytic_ids]:
                        analytic_ids += [{'analytic_id': po_line.account_analytic_id.id,
                                          'rate': po_line.price_subtotal}]
                        total += po_line.price_subtotal
                for a in analytic_ids:
                    a['rate'] = total and (a.get('rate',0.0)/total) or 1.0
        else:
            analytic_ids = [{'analytic_id':analytic_id}]
        for _analytic_id in analytic_ids or [{}]:
            rate = _analytic_id.get('rate',1.0)
            l1 = {
                'move_id': move.id,
                'name': line and line.name or (purchase and purchase.name or (sale and sale.name or move.ref or move.name)),
                'struct_id': struct_id,
            }
            l2 = {
                'move_id': move.id,
                'name': line and line.name or (purchase and purchase.name or (sale and sale.name or move.ref or move.name)),
                'struct_id': struct_id,
            }
            if _analytic_id.has_key('analytic_id'):
                l1['analytic_id'] = _analytic_id['analytic_id']
                l2['analytic_id'] = _analytic_id['analytic_id']
            if line and line.partner_id:
                l1['partner_id'] = line.partner_id.id
                l2['partner_id'] = line.partner_id.id
            elif purchase:
                l2['partner_id'] = purchase.partner_id.id
            elif sale:
                l2['partner_id'] = sale.partner_id.id
            if line and line.move_id.journal_id.type in ('cash', 'bank'):
                l1['provision'] = amount * rate
                l2['paid'] = amount * -1.0 * rate
            elif line and line.move_id.journal_id.type in ('sale', 'sale_refund', 'purchase', 'purchase_refund'):
                l1['committed'] = amount * -1.0 * rate
                l2['provision'] = amount * rate
            elif purchase:
                l1['available'] = amount * rate
                l2['committed'] = amount * -1.0 * rate
            elif sale:
                l1['available'] = amount * -1.0 * rate
                l2['committed'] = amount * rate
            else:
                raise exceptions.ValidationError(_("The journal kind %s is not supported to make automatic budget "
                                                   "transactions. Make a manually budget transaction for the line %s!") %
                                                 (line.move_id.journal_id.type, line.name))
            res += [l1, l2]
        return res

    def create_from_account(self, line):
        move = self.create(self._create_move_values(line))
        for line_dict in self._create_lines_values(move, line):
            self.env['budget.move.line'].create(line_dict)
        return move

    def create_from_po(self, purchase):
        move = self.create(self._create_move_values(purchase=purchase))
        for line_dict in self._create_lines_values(move, purchase=purchase):
            self.env['budget.move.line'].create(line_dict)
        return move

    def create_from_reconcile(self, reconcile_id):
        reconcile = self.env['account.move.reconcile'].browse(reconcile_id)
        cash = []
        prom = {}
        vals = []
        for line in reconcile.line_id:
            if line.journal_id.type in ('cash', 'bank') and not line.budget_struct_id:
                cash += [line]
            elif line.journal_id.type not in ('cash', 'bank') and line.budget_struct_id:
                prom[(line.budget_struct_id.id, line.analytic_account_id.id, line.partner_id.id)] = \
                    prom.get((line.budget_struct_id.id, line.analytic_account_id.id, line.partner_id.id), 0.0) + \
                    (line.debit - line.credit)
                vals.append((line.debit - line.credit))
        total_vals = sum(vals)
        if cash and total_vals:
            for c in cash:
                move = self.create(self._create_move_values(c))
                for k in prom:
                    amount = (c.debit - c.credit) * prom[k] / total_vals
                    for line_dict in self._create_lines_values(move, c, amount=amount, struct_id=k[0],
                                                               analytic_id=k[1]):
                        self.env['budget.move.line'].create(line_dict)

                        # @api.one
                        # @api.onchange('line_ids')
                        # def onchange_line_ids(self):
                        #     name = ''
                        #     last_move_line = period_id = None
                        #     if self.line_ids:# si hay lineas presupuestarias
                        #         last_move_line = self.line_ids.sorted(key=lambda bml: (bml.id, bml.create_date), reverse=True)[0]# me quedo con la ultima
                        #         name = last_move_line.name#nombre de la linea a crear lo tomo de la ultima
                        #     else:# si no hay lineas presupuestarias
                        #         if self.ref:
                        #             name = self.ref
                        #         if self.period_id:
                        #             period_id = self.period_id.id
                        #     self.line_ids.with_context(name=name, period_id=self.period_id.id).default_get(['name'])


class BudgetMoveLine(models.Model):
    _name = "budget.move.line"
    _description = "Budget Move Line"

    name = fields.Char("Name", required=True)
    move_id = fields.Many2one("budget.move", string="Move", required=True, ondelete="cascade")
    period_id = fields.Many2one('budget.period', string="Period", related="move_id.period_id", readonly=True,store=True)
    ref = fields.Char(string="Ref", related="move_id.ref", readonly=True, store=True)
    date = fields.Date(string="Date", related="move_id.date", readonly=True, store=True)
    company_id = fields.Many2one("res.company", related="move_id.company_id", string='Company', store=True,
                                 readonly=True)
    struct_id = fields.Many2one('budget.struct', string="Struct", required=True,
                                domain=[('type', '=', 'normal')])
    analytic_id = fields.Many2one('account.analytic.account', string="Analytic Account")
    partner_id = fields.Many2one('res.partner', string="Partner")
    available = fields.Float("Available")
    committed = fields.Float("Committed")
    provision = fields.Float("Provision")
    paid = fields.Float("Paid")
    state = fields.Selection([('draft', 'Draft'),
                              ('valid', 'Valid')], string="State", readonly=True, default='valid')

    # @api.model
    # def default_get(self, fields):
    #     name, available = '', 0.0
    #     struct = last_line = analytic_id = partner_id = None
    #     line_ids = [line[1] for line in self._context.get('line_ids')]
    #     if line_ids and not line_ids[0]:
    #         line_rec = self.env['budget.move.line'].browse(line_ids)
    #         last_line = line_rec.sorted(key=lambda bml: (bml.id, bml.create_date), reverse=True)[
    #             0]  # me quedo con la ultima
    #         name, struct, available, analytic_id, partner_id = last_line.name, last_line.struct_id.id, last_line.available, last_line.analytic_id.id, last_line.partner_id.id
    #     else:
    #         move_id = self.env['budget.move'].browse(self._context.get('active_id', None))
    #         name = move_id.name
    #     res = super(BudgetMoveLine, self).default_get(fields)
    #     res.update({'name': name, 'struct_id': struct, 'available': available, 'analytic_id': analytic_id,
    #                 'partner_id': partner_id})
    #     return res

    @api.model
    def default_get(self, fields):
        data = self._default_get(fields)
        for f in data.keys():
            if f not in fields:
                del data[f]
        return data

    @api.model
    def _default_get(self, fields):
        move_obj, partner_obj, period_obj = self.env['budget.move'], self.env['res.partner'], self.env['budget.period']
        cr, uid, ctx = self._cr, self._uid, self._context.copy() or {}

        if not ctx.get('line_ids', False):
            ctx.update({'line_ids': ctx.get('search_default_line_ids', False)})

        data = super(BudgetMoveLine, self).default_get(fields)

        if ctx.get('line_ids'):
            for move_line_dict in move_obj.resolve_2many_commands('line_ids', ctx.get('line_ids'), context=ctx):
                data.update({'name': data.get('name') or move_line_dict.get('name'),
                             'partner_id': data.get('partner_id') or move_line_dict.get('partner_id'),
                             'struct_id': data.get('struct_id') or move_line_dict.get('struct_id'),
                             'analytic_id': data.get('analytic_id') or move_line_dict.get('analytic_id'),
                             'available': data.get('available') or move_line_dict.get('available'), })
        elif ctx.get('period_id'):
            move_id = False
            cr.execute('''SELECT move_id, struct_id, date FROM budget_move_line
                WHERE period_id = %s AND struct_id = %s AND create_uid = %s AND state = %s
                ORDER BY id DESC limit 1''', (ctx['period_id'], ctx['struct_id'], uid, 'draft'))
            res = cr.fetchone()
            move_id = res and res[0] or False
            data.update({'date': res and res[1] or period_obj.browse(cr, uid, ctx['period_id'],
                                                                     context=ctx).date_start,
                         'move_id': move_id})
        return data

    @api.model
    def create(self, vals):
        if 'available' in vals or 'committed' in vals or 'provision' in vals or 'paid' in vals:
            res = vals.get('available', 0.0) + vals.get('committed', 0.0) + vals.get('provision', 0.0) + vals.get(
                'paid', 0.0)
            valid_ids = []
            for line in self.env['budget.move'].browse(vals['move_id']).line_ids:
                res += line.available + line.committed + line.provision + line.paid
                valid_ids += line.state == 'draft' and [line] or []
            if res == 0.0:
                vals['state'] = 'valid'
                for line in valid_ids:
                    line.state = 'valid'
            else:
                vals['state'] = 'draft'
        return super(BudgetMoveLine, self).create(vals)

    @api.one
    def write(self, vals):
        if 'available' in vals or 'committed' in vals or 'provision' in vals or 'paid' in vals:
            res = vals.get('available', 0.0) + vals.get('committed', 0.0) + vals.get('provision', 0.0) + vals.get(
                'paid', 0.0)
            move_id = vals.get('move_id', self.move_id.id)
            valid_ids = []
            for line in self.env['budget.move'].browse(move_id).line_ids:
                if line.id <> self.id:
                    res += line.available + line.committed + line.provision + line.paid
                    valid_ids += line.state == 'draft' and [line] or []
            if res == 0.0:
                vals['state'] = 'valid'
                for line in valid_ids:
                    line.state = 'valid'
            else:
                vals['state'] = 'draft'
        return super(BudgetMoveLine, self).write(vals)

    @api.multi
    def unlink(self):
        for del_line in self:
            res = 0.0
            line_ids = []
            for line in del_line.move_id.line_ids:
                if line.id <> del_line.id:
                    res += line.available + line.committed + line.provision + line.paid
                    line_ids += [line]
            if line_ids:
                line_ids.write({'state': res == 0.0 and 'valid' or 'draft'})
        return super(BudgetMoveLine, self).unlink()
