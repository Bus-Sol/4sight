# -*- coding: utf-8 -*-
from odoo import api, fields, models


SKIP_PARTNER_EMAIL_SYNC_CONTEXT_KEY = "4sight_skip_partner_email_sync"


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    hide_from_portal = fields.Boolean(related='team_id.hide_from_portal')

    @api.model
    def message_new(self, msg, custom_values=None):
        """Do not replace a customer's email while creating an inbound ticket."""
        return super(
            HelpdeskTicket,
            self.with_context(**{SKIP_PARTNER_EMAIL_SYNC_CONTEXT_KEY: True}),
        ).message_new(msg, custom_values=custom_values)

    def _inverse_partner_email(self):
        if self.env.context.get(SKIP_PARTNER_EMAIL_SYNC_CONTEXT_KEY):
            return
        return super()._inverse_partner_email()


class HelpdeskTeam(models.Model):
    _inherit = "helpdesk.team"

    hide_from_portal = fields.Boolean('Hide from Portal')
