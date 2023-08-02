# -*- coding: utf-8 -*-
from odoo import fields, models, api, modules, _


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    hide_from_portal = fields.Boolean(related='team_id.hide_from_portal')



class HelpdeskTeam(models.Model):
    _inherit = "helpdesk.team"

    hide_from_portal = fields.Boolean('Hide from Portal')