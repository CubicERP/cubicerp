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

from openerp import models, fields, api
from openerp.exceptions import except_orm

class ir_sequence(models.Model):
    _inherit = "ir.sequence"
    
    @api.multi
    def get_number_by_code(self, doc_number):
        self.ensure_one()
        if doc_number=='/':
            return 0
        d = self._interpolation_dict_context(context=self.env.context)
        try:
            interpolated_prefix = self._interpolate(self.prefix, d) or ''
            interpolated_suffix = self._interpolate(self.suffix, d) or ''
        except ValueError:
            raise except_orm(_('Warning'), _('Invalid prefix or suffix for sequence \'%s\'') % (self.name))
        prefix=len(interpolated_prefix)
        suffix=len(interpolated_suffix)
        number=doc_number
        if prefix>0:
            number=number[prefix:]
        if suffix>0:
            number=number[:-suffix]
        res=0
        try:
            res=int(number)
        except:
            pass
        return res
    