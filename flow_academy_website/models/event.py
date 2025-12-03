from odoo import api, fields, models


class Event(models.Model):
    _inherit = "event.event"

    event_category_id = fields.Many2one(comodel_name="event.category", string="Event Category")
