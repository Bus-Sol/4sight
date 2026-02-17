from odoo import api, fields, models


class Event(models.Model):
    _inherit = "event.event"

    event_category_id = fields.Many2one(comodel_name="event.category", string="Event Category")

    price = fields.Monetary(string="price",  currency_field='currency_id', compute="compute_price")

    start_time = fields.Float(string="Start time")
    end_time = fields.Float(string="End time")

    trainer = fields.Char(string="Trainer")
    location_type = fields.Selection(string="Location", selection=[('ON Site', 'On-site'), ('Online', 'Online'), ])

    @api.depends('event_ticket_ids', 'event_ticket_ids.price')
    def compute_price(self):
        for rec in self:
            rec.price = max(rec.event_ticket_ids.mapped('price')) if rec.event_ticket_ids else 0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # If company_ids not provided, default to current company
            if not vals.get('website_published'):
                vals['website_published'] = True
        return super().create(vals_list)