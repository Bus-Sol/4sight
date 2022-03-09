# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class Designation(models.Model):
    _name = "client.designation"
    _description = "Designation"

    name = fields.Char('Name')