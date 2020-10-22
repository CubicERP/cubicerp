from odoo import models, api


class AccountUnreconcile(models.TransientModel):
    _name = "account.unreconcile"
    _description = "Account Unreconcile"

    @api.multi
    def trans_unrec(self):
        context = dict(self._context or {})
        res = {'type': 'ir.actions.act_window_close'}
        if context.get('active_ids', False) and context.get('active_model') == 'account.move.line':
            self.env['account.move.line'].browse(context.get('active_ids')).remove_move_reconcile()
        elif context.get('active_ids', False) and context.get('active_model') == 'account.full.reconcile':
            self.env['account.full.reconcile'].browse(context['active_ids']).mapped('reconciled_line_ids').remove_move_reconcile()
            res = True
        return res
