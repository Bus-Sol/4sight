# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit = "account.move"

    job_ids = fields.Many2many('client.jobsheet', string='Job Ref')
    job_count = fields.Integer(string='Jobsheets Count', compute='_get_jobsheets', readonly=True)

    @api.depends('job_ids')
    def _get_jobsheets(self):
        for order in self:
            jobsheets = self.env['client.jobsheet'].search([('move_ids', 'in', order.ids)])
            order.job_ids = jobsheets
            order.job_count = len(jobsheets)


    def action_view_jobsheets(self):

        jobsheets = self.mapped('job_ids')
        action = self.env["ir.actions.actions"]._for_xml_id("odoo_timestead.action_jobsheets")
        if len(jobsheets) > 1:
            action['domain'] = [('id', 'in', jobsheets.ids)]
        elif len(jobsheets) == 1:
            form_view = [(self.env.ref('odoo_timestead.view_client_jobsheet_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = jobsheets.id
        else:
            action = {'type': 'ir.actions.act_window_close'}

        context = {}
        if len(self) == 1:
            context.update({
                'default_partner_id': self.partner_id.id,
            })
        action['context'] = context
        return action

    def unlink(self):
        for rec in self:
            if rec.job_ids:
                for job_id in rec.job_ids:
                    if job_id.signature:
                        job_id.status = 'signed'
                    else:
                        job_id.status = 'created'
        return super(AccountMove, self).unlink()

    @api.model
    def create(self, vals):
        res = super(AccountMove, self).create(vals)
        if 'partner_id' in vals:
            list_followers = [res.partner_id.id]
            for child in res.partner_id.child_ids:
                if child.receive_invoice:
                    list_followers.append(child.id)
            res.message_subscribe(partner_ids=list_followers)
        return res