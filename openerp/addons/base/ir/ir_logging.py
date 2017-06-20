##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 OpenERP SA (<http://www.openerp.com>)
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
import logging

from openerp import models, fields, api
from openerp.tools.translate import _

class ir_logging(models.Model):
    _name = 'ir.logging'
    _order = 'id DESC'
    _log_unlink = False

    EXCEPTIONS_TYPE = [
        ('client', 'Client'),
        ('server', 'Server'),
        ('unlink', 'Unlink'),
    ]

    @api.depends('res_model')
    @api.multi
    def _model_id(self):
        for log in self:
            model_ids = self.env['ir.model'].search([('model','=',log.res_model)])
            if model_ids:
                log.model_id = model_ids[0]

    create_date = fields.Datetime('Create Date', readonly=True)
    create_uid = fields.Integer('Uid', readonly=True)
    name = fields .Char('Name', required=True)
    type = fields.Selection(EXCEPTIONS_TYPE, string='Type', required=True, select=True)
    dbname = fields .Char('Database Name', related="group_id.dbname", store=True)
    level = fields .Char('Level', select=True)
    message = fields.Text('Message', required=True)
    path = fields .Char('Path')
    module = fields .Char('Module')
    func = fields .Char('Function')
    line = fields .Char('Line')
    res_id = fields.Integer('Model ID', select=True)
    res_model = fields .Char('Model Name', select=True)
    user_id = fields.Many2one('res.users', "User", related="group_id.user_id", store=True)
    model_id = fields.Many2one('ir.model', "Model", compute=_model_id, store=True)
    group_id = fields.Many2one('ir.logging.group', "Group")

    @api.model
    def log_unlink(self, model, ids):
        vals = {'group_id': self._context.get('logging_group_id'),
                'type': 'unlink',
                'level': 'info',
                'module': "%s%s"%(model._original_module and "%s, "%model._original_module or "", model._module),
                'res_model': model._name,
            }
        cols = []
        for c in model._columns:
            if model._columns[c]._type not in ('one2many','binary','related','many2many','text','html'):
                cols += [c]
        for l in self.env[model._name].browse(ids):
            line = vals.copy()
            try:
                names = l.name_get()
                line['name'] = names and names[0][1] or '*%s'%l.id
            except:
                line['name'] = '*%s'%l.id
                names = False
            line['res_id'] = l.id
            msg = {}
            if names:
                for col in cols:
                    msg[col] = str(getattr(l,col))
            line['message'] = str(msg)
            self.sudo().create(line)
        return True


class ir_logging_group(models.Model):
    _name = 'ir.logging.group'
    _order = 'id DESC'
    _log_unlink = False

    @api.depends('create_uid')
    @api.multi
    def _user_id(self):
        for log in self:
            log.user_id = self.create_uid

    create_date = fields.Datetime('Create Date', readonly=True)
    create_uid = fields.Integer('Uid', readonly=True)  # Integer not m2o is intentionnal
    name = fields.Char('Name', required=True)
    user_id = fields.Many2one('res.users', "User", compute=_user_id, store=True)
    dbname = fields.Char('Database Name', select=True)
    lines = fields.One2many('ir.logging', 'group_id', 'Lines', readonly=True, copy=False)