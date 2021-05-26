# -*- coding: utf-8 -*-
from lxml import etree
from odoo import api, fields, models


class HelpdeskTeam(models.Model):
    _inherit = ['helpdesk.team']

    def _ensure_submit_form_view(self):
        for team in self:
            if not team.website_form_view_id:
                default_form = etree.fromstring(self.env.ref('helpdesk_connect.ticket_submit_form').arch)
                xmlid = 'website_helpdesk_form.team_form_' + str(team.id)
                form_template = self.env['ir.ui.view'].create({
                    'type': 'qweb',
                    'arch': etree.tostring(default_form),
                    'name': xmlid,
                    'key': xmlid
                })
                self.env['ir.model.data'].create({
                    'module': 'website_helpdesk_form',
                    'name': xmlid.split('.')[1],
                    'model': 'ir.ui.view',
                    'res_id': form_template.id,
                    'noupdate': True
                })

                team.write({'website_form_view_id': form_template.id})

class Helpdesk(models.Model):
    _inherit = 'helpdesk.ticket'

    phone = fields.Char('Phone')
    company_name = fields.Char('Company Name')