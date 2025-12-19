from odoo import api, fields, models


class Event(models.Model):
    _inherit = "event.event"

    event_category_id = fields.Many2one(comodel_name="event.category", string="Event Category")

    price = fields.Monetary(string="price",  currency_field='currency_id', compute="compute_price")

    start_time = fields.Float(string="Start time")
    end_time = fields.Float(string="End time")

    @api.depends('event_ticket_ids', 'event_ticket_ids.price')
    def compute_price(self):
        for rec in self:
            rec.price = max(rec.event_ticket_ids.mapped('price')) if rec.event_ticket_ids else 0