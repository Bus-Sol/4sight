# -*- coding: utf-8 -*-
from odoo import models, fields, api


class Helpdesk(models.Model):
    _inherit = "helpdesk.ticket"

    job_id = fields.Many2one('client.jobsheet', 'Related Job')

    def convert_to_job(self):
        job = self.env['client.jobsheet'].create({
            'partner_id': self.partner_id.parent_id.id if self.partner_id.parent_id else self.partner_id.id,
            'brief': self.display_name,
            'project_id': self.partner_id.product_id.project_id.id or False,
            'details': self.description
        })
        self.job_id = job.id