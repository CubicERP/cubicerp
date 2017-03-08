# -*- encoding: utf-8 -*-
##############################################################################
#
#    Branch Cubic ERP, Enterprise Management Software
#    Copyright (C) 2013 Cubic ERP - Teradata SAC (<http://cubicerp.com>).
#
#    This program can only be used with a valid Branch Cubic ERP agreement,
#    it is forbidden to publish, distribute, modify, sublicense or sell 
#    copies of the program.
#
#    The adove copyright notice must be included in all copies or 
#    substancial portions of the program.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT WARRANTY OF ANY KIND; without even the implied warranty
#    of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
##############################################################################

from openerp import api, fields, models, _


class ir_attachment(models.Model):
    _inherit = 'ir.attachment'

    archive_version_id = fields.Many2one('archives.document.version', 'Archives Version',
                                         help="Archives Document Version Asociated")
    parent_id = fields.Many2one('ir.attachment', 'Attachment Template',
                                help="Template required for this attachment")
    isrequired = fields.Boolean('Template Required', help="Especifiy when the specifiyed document is requiered",
                                default=False)

