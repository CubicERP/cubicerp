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

from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.main import _serialize_exception
from odoo.tools import html_escape

import json


class AccountReportController(http.Controller):

    @http.route('/account_report/<string:output_format>/<string:report_name>/<int:report_id>', type='http', auth='user')
    def report(self, output_format, report_name, token, report_id=False, **kw):
        uid = request.session.uid
        domain = [('create_uid', '=', uid)]
        stock_traceability = request.env['account.report.ledger'].sudo(uid).search(domain, limit=1)
        line_data = json.loads(kw['data'])
        try:
            if output_format == 'pdf':
                response = request.make_response(
                    stock_traceability.with_context(active_id=report_id).get_pdf(line_data),
                    headers=[
                        ('Content-Type', 'application/pdf'),
                        ('Content-Disposition', 'attachment; filename=' + 'stock_traceability' + '.pdf;')
                    ]
                )
                response.set_cookie('fileToken', token)
                return response
        except Exception as e:
            se = _serialize_exception(e)
            error = {
                'code': 200,
                'message': 'Cubic ERP Server Error',
                'data': se
            }
            return request.make_response(html_escape(json.dumps(error)))
