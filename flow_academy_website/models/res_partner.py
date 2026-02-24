from odoo import api, fields, models


class Partner(models.Model):
    _inherit = 'res.partner'

    firstname = fields.Char()
    lastname = fields.Char()
    privacy_terms = fields.Boolean(string="Accepted Privacy Terms")
    marketing_subscription = fields.Boolean(string="Marketing Subscription")

