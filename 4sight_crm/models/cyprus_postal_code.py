# -*- coding: utf-8 -*-
from odoo import fields, models, api, modules, _


class CyprusDistrict(models.Model):
    _name = "cyprus.district"

    name = fields.Char('Name')
    key = fields.Char('Key')

class CyprusArea(models.Model):
    _name = "cyprus.area"

    name = fields.Char('Name')
    district_name = fields.Char('District Name')
    key = fields.Char('Key')


