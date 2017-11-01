# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE_OLD file for full copyright and licensing details.

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    sale_note = fields.Text(string='Default Terms and Conditions', translate=True)
