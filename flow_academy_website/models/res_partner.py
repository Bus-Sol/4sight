from odoo import api, fields, models


class Partner(models.Model):
    _inherit = 'res.partner'

    firstname = fields.Char()
    lastname = fields.Char()
