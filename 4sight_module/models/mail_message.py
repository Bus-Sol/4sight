# -*- coding: utf-8 -*-
from odoo import fields, models, api, modules, _


class MAilMessage(models.Model):
    _inherit = "mail.message"

    @api.model
    def create(self, vals):
        res = super(MAilMessage, self).create(vals)
        if res.model == 'helpdesk.ticket':
            ticket_id = self.env['helpdesk.ticket'].browse(res.res_id)
            if ticket_id and vals.get('subtype_id') and vals.get('subtype_id') == self.env.ref('helpdesk.mt_ticket_new').id:
                res.record_name = res.record_name + '- Created by: ' + ticket_id.partner_id.name if ticket_id.partner_id else ticket_id.partner_email
                if ticket_id.description:
                    res.body = ticket_id.description

        return res