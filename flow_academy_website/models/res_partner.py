from odoo import api, fields, models


class Partner(models.Model):
    _inherit = 'res.partner'

    firstname = fields.Char()
    lastname = fields.Char()
    privacy_terms = fields.Boolean(string="Accepted Privacy Terms")
    marketing_subscription = fields.Boolean(string="Marketing Subscription")
    confirm_flow_fund = fields.Boolean(string="Confirm Flow Fund")

