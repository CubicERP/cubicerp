# -*- coding: utf-8 -*-

import random

from odoo import fields, models, api, _


class ScreenBackground(models.Model):
    _name = 'res.config.settings.screen_background'

    image = fields.Binary(string='Background')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    screen_background_ids = fields.Many2many('res.config.settings.screen_background', string='Backgrounds')

    @api.model
    def get_random_background(self):
        params = self.env['ir.config_parameter'].sudo()
        ids = eval(params.get_param('web_responsive.screen_background_ids', '[]'))
        if ids:
            id_selected = random.randint(0, len(ids) - 1)
            return self.screen_background_ids.browse(ids[id_selected]).read([])[0]

        return False

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()

        res.update(
            screen_background_ids=eval(params.get_param('web_responsive.screen_background_ids', '[]'))
        )
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        params = self.env['ir.config_parameter'].sudo()

        self.screen_background_ids.search([('id', 'not in', self.screen_background_ids.ids)]).unlink()

        params.set_param("web_responsive.screen_background_ids", str(self.screen_background_ids.ids))
