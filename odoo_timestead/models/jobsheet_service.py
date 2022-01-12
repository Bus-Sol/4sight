# -*- coding: utf-8 -*-
from odoo import models, fields, api


class JobSheetService(models.Model):
    _name = "jobsheet.service"

    product_id = fields.Many2one('product.template', string='Service', domain=[('type','=', 'service')])
    quantity= fields.Float('Quantity')
    hour = fields.Float('Price')
    buffer = fields.Integer('Buffer (in %)')
    extra_hour = fields.Float('Extra Hour', compute="compute_extra_hour_based_on_buffer", store=True)

    @api.onchange('buffer')
    def compute_extra_hour_based_on_buffer(self):
        for rec in self:
            if rec.buffer:
                rec.extra_hour = rec.quantity * (rec.buffer / 100)
            else:
                rec.extra_hour = 0

