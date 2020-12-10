# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE_LGPL file for full copyright and licensing details.

from odoo import api, fields, models


class AccountAnalyticTag(models.Model):
    _name = 'account.analytic.tag'
    _description = 'Analytic Tags'
    name = fields.Char(string='Analytic Tag', index=True, required=True)
    color = fields.Char('Color Index', default='10')
    active = fields.Boolean(default=True, help="Set active to false to hide the Analytic Tag without removing it.")


class AccountAnalyticAccount(models.Model):
    _name = 'account.analytic.account'
    _inherit = ['mail.thread']
    _description = 'Analytic Account'
    _order = 'code, full_name asc'

    @api.multi
    def _compute_debit_credit_balance(self):
        analytic_line_obj = self.env['account.analytic.line']
        domain = [('account_id', 'in', self.ids)]
        if self._context.get('from_date', False):
            domain.append(('date', '>=', self._context['from_date']))
        if self._context.get('to_date', False):
            domain.append(('date', '<=', self._context['to_date']))

        credit_groups = analytic_line_obj.read_group(
            domain=domain + [('amount', '>=', 0.0)],
            fields=['account_id', 'amount'],
            groupby=['account_id']
        )
        data_credit = {l['account_id'][0]: l['amount'] for l in credit_groups}
        debit_groups = analytic_line_obj.read_group(
            domain=domain + [('amount', '<', 0.0)],
            fields=['account_id', 'amount'],
            groupby=['account_id']
        )
        data_debit = {l['account_id'][0]: l['amount'] for l in debit_groups}

        for account in self:
            account.debit = abs(data_debit.get(account.id, 0.0))
            account.credit = data_credit.get(account.id, 0.0)
            account.balance = account.credit - account.debit

    @api.depends("parent_id","name")
    def _full_name(self):
        for analytic in self:
            analytic.full_name = self._get_full(analytic)

    name = fields.Char(string='Analytic Account', index=True, required=True, track_visibility='onchange')
    full_name = fields.Char('Analytic Account', compute=_full_name, store=True)
    code = fields.Char(string='Reference', index=True, track_visibility='onchange')
    active = fields.Boolean('Active', help="If the active field is set to False, it will allow you to hide the account without removing it.", default=True)
    parent_id = fields.Many2one("account.analytic.account", string="Analytic Parent", domain=[('type','=','view')], index=True)
    child_ids = fields.One2many("account.analytic.account", "parent_id", string="Analytic Childs")
    type = fields.Selection([('normal','Normal'),('view','View')], string="Type", default='normal', required=True, index=True)

    tag_ids = fields.Many2many('account.analytic.tag', 'account_analytic_account_tag_rel', 'account_id', 'tag_id', string='Tags', copy=True)
    line_ids = fields.One2many('account.analytic.line', 'account_id', string="Analytic Lines")

    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id)

    # use auto_join to speed up name_search call
    partner_id = fields.Many2one('res.partner', string='Customer', auto_join=True, track_visibility='onchange')

    balance = fields.Monetary(compute='_compute_debit_credit_balance', string='Balance')
    debit = fields.Monetary(compute='_compute_debit_credit_balance', string='Debit')
    credit = fields.Monetary(compute='_compute_debit_credit_balance', string='Credit')

    currency_id = fields.Many2one(related="company_id.currency_id", string="Currency", readonly=True)

    def name_get(self):
        res = []
        for analytic in self:
            res.append((analytic.id, self._get_full(analytic)))
        return res

    def _get_full(self, e, level=5):
        if level<=0:
            return '...'
        if e.parent_id:
            parent_path = self._get_full(e.parent_id, level-1) + " / "
        else:
            parent_path = ''
        return parent_path + "%s%s%s"%(e.code and '[%s] '%e.code or '',
                                       e.name,
                                       e.partner_id and ' - %s'%e.partner_id.name or '')

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if operator not in ('ilike', 'like', '=', '=like', '=ilike'):
            return super(AccountAnalyticAccount, self).name_search(name, args, operator, limit)
        args = args or []
        domain = ['|', ('code', operator, name), ('name', operator, name)]
        partners = self.env['res.partner'].search([('name', operator, name)], limit=limit)
        if partners:
            domain = ['|'] + domain + [('partner_id', 'in', partners.ids)]
        recs = self.search(domain + args, limit=limit)
        return recs.name_get()


class AccountAnalyticLine(models.Model):
    _name = 'account.analytic.line'
    _description = 'Analytic Line'
    _order = 'date desc, id desc'

    @api.model
    def _default_user(self):
        return self.env.context.get('user_id', self.env.user.id)

    name = fields.Char('Description', required=True)
    date = fields.Date('Date', required=True, index=True, default=fields.Date.context_today)
    amount = fields.Monetary('Amount', required=True, default=0.0)
    unit_amount = fields.Float('Quantity', default=0.0)
    account_id = fields.Many2one('account.analytic.account', 'Analytic Account', required=True, ondelete='restrict', index=True)
    partner_id = fields.Many2one('res.partner', string='Partner')
    user_id = fields.Many2one('res.users', string='User', default=_default_user)

    tag_ids = fields.Many2many('account.analytic.tag', 'account_analytic_line_tag_rel', 'line_id', 'tag_id', string='Tags', copy=True)

    company_id = fields.Many2one(related='account_id.company_id', string='Company', store=True, readonly=True)
    currency_id = fields.Many2one(related="company_id.currency_id", string="Currency", readonly=True)
