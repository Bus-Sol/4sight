# -*- coding: utf-8 -*-

from odoo import fields, models


class Company(models.Model):
    _inherit = 'res.company'

    inv_after_sign = fields.Boolean("Invoice jobsheet only when it is signed")
    jobsheet_manager = fields.Many2one('res.users', string="Jobsheet Manager", domain=lambda self: [
        ('groups_id', 'in', self.env.ref('odoo_timestead.group_jobsheet_manager').id)])
