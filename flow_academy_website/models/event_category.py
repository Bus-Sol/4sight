from odoo import api, fields, models


class EventCategory(models.Model):
    _name = 'event.category'
    _rec_name = 'name'

    name = fields.Char()

    cover = fields.Binary(string="Cover", attachment=True)

    info_link = fields.Char(string="Info Link")
