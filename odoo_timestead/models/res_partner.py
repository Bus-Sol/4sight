# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    monthly_hours = fields.Float(string='Monthly Hours', digits='Product Unit of Measure')
    product_id = fields.Many2one('product.template', string='Service', domain=[('type','=', 'service'),('service_tracking', '!=', 'no')])
    type = fields.Selection(selection_add=[('jobsheet', 'Jobsheet Address')])
    receive_jobsheet = fields.Boolean('Receive Jobsheet')
    receive_invoice = fields.Boolean('Receive Invoice')
    service_ids = fields.One2many('jobsheet.service', 'partner_service_id', string='Related services')
    jobsheet_type = fields.Selection([('prepaid','Prepaid'),('contract_postpaid','Contract/Postpaid')])
    check_balance = fields.Selection([('balanced','Balanced'),('out_of_balance','Out Of Balance')], store=True)
    compute_balance = fields.Boolean(compute='compute_balance_partner')


    def compute_balance_partner(self):
        for rec in self.env['res.partner'].search([('jobsheet_type','=','prepaid')]):
            compute_balance = False
            tasks = self.env['project.task'].search([('partner_id','=',rec.id)])
            if any(task.remaining_hours > 0 for task in tasks):
                compute_balance = True
                rec.check_balance = 'balanced'
            else:
                rec.check_balance = 'out_of_balance'
            rec.compute_balance = compute_balance

    def write(self, vals):
        res = super(ResPartner, self).write(vals)
        if 'child_ids' in vals:
            for child_id in self.child_ids:
                job_ids = self.env['client.jobsheet'].search([('partner_id', '=', child_id.parent_id.id)])
                for job in job_ids:
                    if child_id.receive_jobsheet:
                        job.sudo().message_subscribe(partner_ids=[child_id.id])
                    else:
                        job.sudo().message_unsubscribe(partner_ids=[child_id.id])
                invoice_ids = self.env['account.move'].search([('partner_id', '=', child_id.parent_id.id)])
                for inv in invoice_ids:
                    if child_id.receive_invoice:
                        inv.message_subscribe(partner_ids=[child_id.id])
                    else:
                        inv.message_unsubscribe(partner_ids=[child_id.id])

        return res



class Task(models.Model):
    _inherit = "project.task"

    @api.depends('effective_hours', 'subtask_effective_hours', 'planned_hours')
    def _compute_remaining_hours(self):
        for task in self:
            task.remaining_hours = task.planned_hours - task.effective_hours - task.subtask_effective_hours
            if task.partner_id.jobsheet_type == 'prepaid':
                if task.remaining_hours <=0:
                    task.partner_id.check_balance = 'out_of_balance'
                else:
                    task.partner_id.check_balance = 'balanced'