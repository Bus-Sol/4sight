# -*- coding: utf-8 -*-
from odoo import models, fields, api


class JobSheetService(models.Model):
    _name = "jobsheet.service"

    product_id = fields.Many2one('product.template', string='Service', domain=[('type', '=', 'service')])
    partner_service_id = fields.Many2one('res.partner', required=True, ondelete='cascade', index=True, copy=False)
    quantity = fields.Float('Quantity')
    hour = fields.Float('Price')
    buffer = fields.Integer('Buffer (in %)')
    extra_hour = fields.Float('Extra Hour', compute="compute_extra_hour_based_on_buffer", store=True)
    jobsheet_type = fields.Selection(related='partner_service_id.jobsheet_type')

    @api.onchange('buffer')
    def compute_extra_hour_based_on_buffer(self):
        for rec in self:
            if rec.buffer:
                rec.extra_hour = rec.quantity * (rec.buffer / 100)
            else:
                rec.extra_hour = 0
