# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Cubic ERP SAC (<http://cubicerp.com>).
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

from openerp import api, models

class report_picking_cost(models.AbstractModel):
    _name = 'report.stock_landed_costs.report_picking_cost'
    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('stock_landed_costs.report_picking_cost')
        docargs = {
            'doc_ids': self._ids,
            'doc_model': report.model,
            'docs': self.env[report.model].browse(self._ids),
            'get_cost': self.get_cost,
            'get_line': self.get_line,
            'get_cost_lines': self.get_cost_lines,
        }
        return report_obj.render('stock_landed_costs.report_picking_cost', docargs)
    
    def get_cost(self, landed_costs_ids):
        res = {'names': '',
               'total': 0.0,
               }
        for cost in landed_costs_ids:
            res['names'] += cost.name + " / "
            res['total'] += cost.amount_total
        res['names'] = res['names'] and res['names'][:-3] or ""
        return res
    
    def get_line(self, line):
        res = {'cif': 0.0,
               'total': line.price_unit * line.product_qty,
               }
        for cost in line.picking_id.landed_costs_ids:
            for val in cost.valuation_adjustment_lines:
                if val.product_id.id == line.product_id.id:
                    res['cif'] += val.additional_landed_cost
                    res['total'] += (val.additional_landed_cost * line.product_qty)
        return res
        
    def get_cost_lines(self, landed_costs_ids):
        res = []
        for cost in landed_costs_ids:
            for line in cost.cost_lines:
                res.append(line)
        return res