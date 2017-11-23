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

from odoo import api, models, _
from odoo.exceptions import UserError


class AccountCommonReport(models.TransientModel):
    _inherit = "account.common.report"

    @api.multi
    def preview_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to', 'journal_ids', 'target_move'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang') or 'en_US')
        return self._preview_report(data)

    def _preview_report(self, data):
        raise NotImplementedError()

    def client_action(self, xml_id, data):
        ctx = self._context.copy()
        ctx['data'] = data
        return {'type': 'ir.actions.client',
                'name': self.env.ref(xml_id).name,
                'tag': self.env.ref(xml_id).tag,
                'id': self.env.ref(xml_id).id,
                'xml_id': xml_id,
                'context': ctx,
                }