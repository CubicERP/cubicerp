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

import numpy
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _

# ---------------------------------------------------------
# Account Financial Report
# ---------------------------------------------------------

class account_financial_report(osv.osv):
    _name = "account.financial.report"
    _description = "Account Report"

    def _get_level(self, cr, uid, ids, field_name, arg, context=None):
        '''Returns a dictionary with key=the ID of a record and value = the level of this  
            record in the tree structure.'''
        res = {}
        for report in self.browse(cr, uid, ids, context=context):
            level = 0
            if report.parent_id:
                level = report.parent_id.level + 1
            res[report.id] = level
        return res

    def _get_children_by_order(self, cr, uid, ids, context=None):
        '''returns a dictionary with the key= the ID of a record and value = all its children,
           computed recursively, and sorted by sequence. Ready for the printing'''
        res = []
        for id in ids:
            res.append(id)
            ids2 = self.search(cr, uid, [('parent_id', '=', id)], order='sequence ASC', context=context)
            res += self._get_children_by_order(cr, uid, ids2, context=context)
        return res

    def _get_multiplan_list(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        local_context = context.copy()
        vals = dict((i, []) for i in ids)
        if context.get("multiplan", '') == 'financial':
            for chart_account_id in context.get('multiplan_financial_ids',[]):
                local_context['chart_account_id'] = chart_account_id
                for k, v in self._get_balance(cr, uid, ids, ['balance'], [], context=local_context).iteritems():
                    vals[k] += [v['balance']]
        elif context.get("multiplan", '') == 'analytic':
            for analytic_id in context.get('multiplan_analytic_ids',[]):
                local_context['analytic_account_id'] = analytic_id
                for k, v in self._get_balance(cr, uid, ids, ['balance'], [], context=local_context).iteritems():
                    vals[k] += [v['balance']]
        elif context.get("multiplan", '') == 'period':
            for period_id in context.get('multiplan_period_ids', []):
                for ff in ['date_from', 'date_to']:
                    if local_context.has_key(ff):
                        del local_context[ff]
                local_context['period_from'] = period_id
                local_context['period_to'] = period_id
                for k, v in self._get_balance(cr, uid, ids, ['balance'], [], context=local_context).iteritems():
                    vals[k] += [v['balance']]
        return vals

    def _get_multiplan(self, cr, uid, ids, field_names, args, context=None):
        res = self._get_multiplan_list(cr, uid, ids, context=context)
        for k, v in res.iteritems():
            res[k] = str(v)
        return res

    def _get_values(self, cr, uid, report, field_names, context=None):
        account_obj = self.pool.get('account.account')
        vals = {}
        if report.type == 'accounts':
            # it's the sum of the linked accounts
            for a in account_obj.browse(cr, uid, [a.id for a in report.account_ids], context=context):
                for field in field_names:
                    vals[field] = vals.get(field,[]) + [getattr(a, field) * report.sign]
        elif report.type == 'account_type':
            # it's the sum the leaf accounts with such an account type
            report_types = [x.id for x in report.account_type_ids]
            account_ids = account_obj.search(cr, uid, [('user_type', 'in', report_types), ('type', '!=', 'view')],
                                             context=context)
            for a in account_obj.browse(cr, uid, account_ids, context=context):
                for field in field_names:
                    vals[field] = vals.get(field,[]) + [getattr(a, field) * report.sign]
        elif report.type == 'account_report' and report.account_report_ids:
            # it's the amount of the linked report
            res2 = self._get_balance(cr, uid, [r.id for r in report.account_report_ids], field_names, False,
                                     context=context)
            for key, value in res2.items():
                for field in field_names:
                    vals[field] = vals.get(field,[]) + [value[field] * report.sign]
        elif report.type == 'sum':
            # it's the sum of the children of this account.report
            res2 = self._get_balance(cr, uid, [rec.id for rec in report.children_ids], field_names, False,
                                     context=context)
            for key, value in res2.items():
                for field in field_names:
                    vals[field] = vals.get(field,[]) + [value[field]]
        return vals



    def _get_balance(self, cr, uid, ids, field_names, args, context=None):
        '''returns a dictionary with key=the ID of a record and value=the balance amount 
           computed for this record. If the record is of type :
               'accounts' : it's the sum of the linked accounts
               'account_type' : it's the sum of leaf accoutns with such an account_type
               'account_report' : it's the amount of the related report
               'sum' : it's the sum of the children of this record (aka a 'view' record)'''

        res = {}
        for report in self.browse(cr, uid, ids, context=context):
            if report.id in res:
                continue
            res[report.id] = dict((fn, 0.0) for fn in field_names)
            ctx = context.copy()
            if report.analytic_ids and (report.type == 'accounts' or report.type == 'account_type'):
                ctx['analytic_account_id'] = [a.id for a in report.analytic_ids]
            if report.tax_included and report.tax_account_ids and (report.type == 'accounts' or report.type == 'account_type'):
                ctx['tax_account_ids'] = [a.id for a in report.tax_account_ids]
            vals = self._get_values(cr, uid, report, field_names, context=ctx)
            for field in field_names:
                if report.aggregate == 'sum':
                    res[report.id][field] = sum(vals.get(field,[]))
                elif report.aggregate == 'avg':
                    v = vals.get(field, [])
                    res[report.id][field] = v and sum(v)/len(v) or 0.0
                elif report.aggregate == 'max':
                    res[report.id][field] = max(vals.get(field, []))
                elif report.aggregate == 'min':
                    res[report.id][field] = min(vals.get(field, []))
                elif report.aggregate == 'std':
                    res[report.id][field] = numpy.std(vals.get(field, []))
                elif report.aggregate == 'var':
                    res[report.id][field] = numpy.var(vals.get(field, []))
        return res

    def _get_full_name(self, cr, uid, ids, name=None, args=None, context=None):
        if context == None:
            context = {}
        res = {}
        for elmt in self.browse(cr, uid, ids, context=context):
            res[elmt.id] = self._get_one_full_name(elmt)
        return res

    def _get_one_full_name(self, elmt, level=6):
        if level <= 0:
            return '...'
        if elmt.parent_id:
            parent_path = self._get_one_full_name(elmt.parent_id, level - 1) + " / "
        else:
            parent_path = ''
        return parent_path + elmt.name

    def _get_types(self, cr, uid, context=None):
        return [('sum','View'),
            ('accounts','Accounts'),
            ('account_type','Account Type'),
            ('account_report','Report Value')]

    _columns = {
        'name': fields.char('Report Name', required=True, translate=True),
        'parent_id': fields.many2one('account.financial.report', 'Parent', domain=[('type','=','sum')]),
        'children_ids':  fields.one2many('account.financial.report', 'parent_id', 'Account Report'),
        'complete_name': fields.function(_get_full_name, type='char', string='Full Name'),
        'sequence': fields.integer('Sequence'),
        'balance': fields.function(_get_balance, 'Balance', multi='balance'),
        'debit': fields.function(_get_balance, 'Debit', multi='balance'),
        'credit': fields.function(_get_balance, 'Credit', multi="balance"),
        'multiplan': fields.function(_get_multiplan, 'Multiplan List', type="char"),
        'level': fields.function(_get_level, string='Level', store=True, type='integer'),
        'type': fields.selection(_get_types,'Type'),
        'account_ids': fields.many2many('account.account', 'account_account_financial_report', 'report_line_id', 'account_id', 'Accounts'),
        'account_report_ids':  fields.many2many('account.financial.report', 'account_finan_report_account_report', 'report_id', 'parent_id','Report Values'),
        'analytic_ids':  fields.many2many('account.analytic.account', 'account_finan_report_account_analytic', 'report_id', 'analytic_id','Analytic Accounts'),
        'account_type_ids': fields.many2many('account.account.type', 'account_account_financial_report_type', 'report_id', 'account_type_id', 'Account Types'),
        'tax_included': fields.boolean("Tax Included"),
        'tax_account_ids': fields.many2many('account.account', 'account_tax_financial_report', 'report_line_id', 'account_id', 'Tax Accounts'),
        'sign': fields.selection([(-1, 'Reverse balance sign'), (1, 'Preserve balance sign')], 'Sign on Reports', required=True, help='For accounts that are typically more debited than credited and that you would like to print as negative amounts in your reports, you should reverse the sign of the balance; e.g.: Expense account. The same applies for accounts that are typically more credited than debited and that you would like to print as positive amounts in your reports; e.g.: Income account.'),
        'aggregate': fields.selection([('sum','Sum'),
                                       ('avg','Average'),
                                       ('max','Maximum'),
                                       ('min','Minimum'),
                                       ('std','Standard Deviation'),
                                       ('var','Variance')], "Agregate Function", required=True),
        'display_detail': fields.selection([
            ('no_detail','No detail'),
            ('detail_flat','Display children flat'),
            ('detail_with_hierarchy','Display children with hierarchy')
            ], 'Display details'),
        'style_overwrite': fields.selection([
            (0, 'Automatic formatting'),
            (1,'Main Title 1 (bold, underlined)'),
            (2,'Title 2 (bold)'),
            (3,'Title 3 (bold, smaller)'),
            (4,'Normal Text'),
            (5,'Italic Text (smaller)'),
            (6,'Smallest Text'),
            ],'Financial Report Style', help="You can set up here the format you want this record to be displayed. If you leave the automatic formatting, it will be computed based on the financial reports hierarchy (auto-computed field 'level')."),
    }

    _order = "sequence,name"

    _defaults = {
        'type': 'sum',
        'display_detail': 'detail_flat',
        'sign': 1,
        'aggregate': 'sum',
        'style_overwrite': 0,
    }


    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        if isinstance(ids, (int, long)):
            ids = [ids]
        reads = self.read(cr, uid, ids, ['name', 'sequence'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['sequence']:
                name = str(record['sequence']) + ' ' + name
            res.append((record['id'], name))
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
