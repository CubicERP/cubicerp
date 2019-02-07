# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE_LGPL file for full copyright and licensing details.

from odoo import api, models, fields
from odoo.exceptions import AccessError


class Partner(models.Model):

    _inherit = ['res.partner']


    @api.depends('employee_ids.address_home_id')
    def _employee_id(self):
        for partner in self.filtered(lambda p: not p.is_company):
            partner.employee_id = partner.employee_ids and partner.employee_ids[0] or False

    def _inv_employee_id(self):
        if self.employee_id:
            self.employee_id.write({'address_home_id': self.id})
        else:
            self.env['hr.employee'].search([('address_home_id','=',self.id)]).write({'address_home_id': False})


    employee_id = fields.Many2one("hr.employee", compute=_employee_id, inverse=_inv_employee_id)
    employee_ids = fields.One2many("hr.employee", "address_home_id")

    @api.model
    def get_static_mention_suggestions(self):
        """ Extend the mail's static mention suggestions by adding the employees. """
        suggestions = super(Partner, self).get_static_mention_suggestions()

        try:
            employee_group = self.env.ref('base.group_user')
            hr_suggestions = [{'id': user.partner_id.id, 'name': user.name, 'email': user.email}
                              for user in employee_group.users]
            suggestions.append(hr_suggestions)
            return suggestions
        except AccessError:
            return suggestions
