# -*- coding: utf-8 -*-

from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    inv_after_sign = fields.Boolean(related='company_id.inv_after_sign', readonly=False,
                                    string='Invoice Jobsheet only when it is signed')
    # module_jobsheet_project = fields.Boolean("Use Project in Jobsheets", store=True, readonly=False)
    jobsheet_manager = fields.Many2one('res.users', related='company_id.jobsheet_manager', string="Jobsheet Manager",
                                       readonly=False)
