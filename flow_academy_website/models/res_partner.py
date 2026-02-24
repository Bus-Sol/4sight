from odoo import api, fields, models


class Partner(models.Model):
    _inherit = 'res.partner'

    firstname = fields.Char()
    lastname = fields.Char()
    marketing_subscription = fields.Boolean(string="Marketing Subscription")

