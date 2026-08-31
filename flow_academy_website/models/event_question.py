from odoo import fields, models


class EventQuestion(models.Model):
    _inherit = "event.question"

    food_allergies = fields.Boolean(string="Food Allergies")
