# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from random import randint
from odoo.exceptions import ValidationError


class JobSheetTags(models.Model):
    _name = "jobsheet.tags"
    _description = 'Jobsheet Tags'
    _order = 'name'

    def _get_default_color(self):
        return randint(1, 11)

    name = fields.Char(string='Tag Name', required=True, translate=True)
    color = fields.Integer(string='Color Index', default=_get_default_color)
    active = fields.Boolean(default=True, help="The active field allows you to hide the category without removing it.")
    jobsheet_ids = fields.Many2many('client.jobsheet', column1='category_id', column2='jobsheet_id', string='Jobsheets')

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        if name:
            # Be sure name_search is symetric to name_get
            name = name.split(' / ')[-1]
            args = [('name', operator, name)] + args
        return self._search(args, limit=limit, access_rights_uid=name_get_uid)
