from odoo import api, fields, models


class MailingList(models.Model):
    _inherit = 'mailing.list'

    is_flow = fields.Boolean(string="Flow Academy List")
