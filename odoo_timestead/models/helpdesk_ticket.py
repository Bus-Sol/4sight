# -*- coding: utf-8 -*-
from odoo import models, fields, api


class Helpdesk(models.Model):
    _inherit = "helpdesk.ticket"

    job_id = fields.Many2one('client.jobsheet', 'Related Job')


    def action_view_job(self):

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('odoo_timestead.view_client_jobsheet_form').id,
            'res_model': 'client.jobsheet',
            'res_id': self.job_id.id,
            'target': 'current',
        }

    def convert_to_job(self):

        action = self.env["ir.actions.actions"]._for_xml_id("odoo_timestead.action_jobsheets")
        action['context'] = {
            'default_ticket_id': self.id,
            'search_default_partner_id': self.partner_id.parent_id.id if self.partner_id.parent_id else self.partner_id.id,
            'default_partner_id': self.partner_id.parent_id.id if self.partner_id.parent_id else self.partner_id.id,
            'default_brief': self.display_name,
            'default_project_id': self.partner_id.product_id.project_id.id or False,
            'default_details': self.description,
            'default_company_id': self.company_id.id or self.env.company.id,
        }
        action['views'] = [[self.env.ref('odoo_timestead.view_client_jobsheet_form').id, 'form']]
        return action