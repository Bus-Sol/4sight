# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class JobsheetType(models.Model):
    _name = "jobsheet.type"
    _description = "Jobsheet Type"

    name = fields.Char('Description')
    nominal_code = fields.Selection([('4100', '4100'), ('sales', 'Sales')])
    tax_code = fields.Selection([('18vat', '18vat'), ('s1', 'S1')])
    active = fields.Boolean('Active', default=True)
