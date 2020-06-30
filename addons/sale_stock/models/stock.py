# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE_LGPL file for full copyright and licensing details.

from odoo import api, fields, models, exceptions, _


class StockLocationRoute(models.Model):
    _inherit = "stock.location.route"
    sale_selectable = fields.Boolean("Selectable on Sales Order Line")


class StockMove(models.Model):
    _inherit = "stock.move"
    sale_line_id = fields.Many2one('sale.order.line', 'Sale Line')
    invoice_line_id = fields.Many2one("account.invoice.line", copy=False,
                                      help="Technical field to print picking name in invoices")

    @api.model
    def _prepare_merge_moves_distinct_fields(self):
        distinct_fields = super(StockMove, self)._prepare_merge_moves_distinct_fields()
        distinct_fields.append('sale_line_id')
        return distinct_fields

    @api.model
    def _prepare_merge_move_sort_method(self, move):
        move.ensure_one()
        keys_sorted = super(StockMove, self)._prepare_merge_move_sort_method(move)
        keys_sorted.append(move.sale_line_id.id)
        return keys_sorted

    def _action_done(self):
        result = super(StockMove, self)._action_done()
        for line in result.mapped('sale_line_id').sudo():
            line.qty_delivered = line._get_delivered_qty()
        return result

    @api.multi
    def write(self, vals):
        res = super(StockMove, self).write(vals)
        if 'product_uom_qty' in vals:
            for move in self:
                if move.state == 'done':
                    sale_order_lines = self.filtered(lambda move: move.sale_line_id and move.product_id.expense_policy in [False, 'no']).mapped('sale_line_id')
                    for line in sale_order_lines.sudo():
                        line.qty_delivered = line._get_delivered_qty()
        return res

    def _assign_picking_post_process(self, new=False):
        super(StockMove, self)._assign_picking_post_process(new=new)
        if new and self.sale_line_id and self.sale_line_id.order_id:
            self.picking_id.message_post_with_view(
                'mail.message_origin_link',
                values={'self': self.picking_id, 'origin': self.sale_line_id.order_id},
                subtype_id=self.env.ref('mail.mt_note').id)


class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    sale_id = fields.Many2one('sale.order', 'Sale Order')


class ProcurementRule(models.Model):
    _inherit = 'procurement.rule'

    def _get_stock_move_values(self, product_id, product_qty, product_uom, location_id, name, origin, values, group_id):
        result = super(ProcurementRule, self)._get_stock_move_values(product_id, product_qty, product_uom, location_id, name, origin, values, group_id)
        if values.get('sale_line_id', False):
            result['sale_line_id'] = values['sale_line_id']
        return result


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    sale_id = fields.Many2one(related="group_id.sale_id", string="Sales Order", store=True)

    def get_picking_name(self):
        self.ensure_one()
        return self.name

    def action_fix_sale_line(self):
        group = self.mapped('group_id')
        if len(group) != 1:
            raise exceptions.ValidationError(_("Procurement group must be unique!"))
        if not group.sale_id:
            raise exceptions.ValidationError(
                _("There isn't a sale order associated to the procurement group %s")%group.name)
        lines = group.sale_id.order_line
        to_update = self.env['sale.order.line']
        for picking in self.filtered(lambda p: p.state != 'cancel'):
            for move in picking.move_lines.filtered(lambda m: not m.sale_line_id or m.sale_line_id not in lines):
                if move.sale_line_id:
                    to_update |= move.sale_line_id
                for line in lines.filtered(lambda l: l.product_id == move.product_id):
                    move.write({'sale_line_id': line.id, 'group_id': group.id})
                    to_update |= line
                    break
                else:
                    raise exceptions.ValidationError(
                        _("Product %s not found in the sale order %s") % (move.product_id.name, group.sale_id.name))

        for line in to_update.sudo():
            line.qty_delivered = line._get_delivered_qty()


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    print_number = fields.Boolean(help="Print picking number in the invoice")