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

from openerp import tools
from openerp.osv import fields, osv

class sale_report(osv.osv):
    _name = "sale.report"
    _inherit = "sale.report"

    def _select2(self):
        select_str = """
                UNION ALL
                 SELECT min(l.id)*-1 as id,
                        l.product_id as product_id,
                        t.uom_id as product_uom,
                        sum(l.qty) as product_uom_qty,
                        sum(l.qty * l.price_unit * (100.0-l.discount) / 100.0) as price_total,
                        count(*) as nbr,
                        s.date_order as date,
                        s.date_order as date_confirm,
                        s.partner_id as partner_id,
                        s.user_id as user_id,
                        s.company_id as company_id,
                        extract(epoch from avg(date_trunc('day',s.date_order)-date_trunc('day',s.create_date)))/(24*60*60)::decimal(16,2) as delay,
                        s.state,
                        t.categ_id as categ_id,
                        s.pricelist_id as pricelist_id,
                        0 as analytic_account_id,
                        0 as section_id
                        , 1 as warehouse_id, true as shipped, 1 as shipped_qty_1
        """
        return select_str + super(sale_report, self)._select2()

    def _from2(self):
        from_str = """
                FROM pos_order_line l
                     join pos_order s on (l.order_id=s.id)
                       left join product_product p on (l.product_id=p.id)
                          left join product_template t on (p.product_tmpl_id=t.id)
        """
        return from_str + super(sale_report, self)._from2()

    def _group_by2(self):
        group_by_str = """
                 GROUP BY l.product_id,
                        l.order_id,
                        t.uom_id,
                        t.categ_id,
                        s.date_order,
                        s.date_order,
                        s.partner_id,
                        s.user_id,
                        s.company_id,
                        s.state,
                        s.pricelist_id
        """
        return group_by_str + super(sale_report, self)._group_by2() 
