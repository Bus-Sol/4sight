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
    job_count = fields.Integer("Jobsheets", compute='_compute_job_count')

    def _compute_job_count(self):
        # retrieve all children partners and prefetch 'parent_id' on them
        all_partners = self.with_context(active_test=False).search([('id', 'child_of', self.ids)])
        all_partners.read(['parent_id'])

        # group tickets by partner, and account for each partner in self
        groups = self.env['client.jobsheet'].read_group(
            [('partner_id', 'in', all_partners.ids)],
            fields=['partner_id'], groupby=['partner_id'],
        )
        self.job_count = 0
        for group in groups:
            partner = self.browse(group['partner_id'][0])
            while partner:
                if partner in self:
                    partner.job_count += group['partner_id_count']
                partner = partner.parent_id

    def action_open_jobsheet(self):
        action = self.env["ir.actions.actions"]._for_xml_id("odoo_timestead.action_jobsheets")
        action['context'] = {}
        action['domain'] = [('partner_id', 'child_of', self.ids)]
        return action

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

    jobsheet_type = fields.Selection(related='partner_id.jobsheet_type')
    check_balance = fields.Selection([('balanced','Balanced'),('out_of_balance','Out Of Balance')], string='Check Balance',compute='compute_balanced_task', store=True)

    @api.depends('remaining_hours')
    def compute_balanced_task(self):
        for rec in self:
            check_balance = False
            if rec.remaining_hours > 0 :
                check_balance = 'balanced'
            else:
                check_balance = 'out_of_balance'
            rec.check_balance = check_balance


#     @api.depends('effective_hours', 'subtask_effective_hours', 'planned_hours')
#     def _compute_remaining_hours(self):
#         for task in self:
#             task.remaining_hours = task.planned_hours - task.effective_hours - task.subtask_effective_hours
#             if task.partner_id.jobsheet_type == 'prepaid':
#                 if task.remaining_hours <=0:
#                     task.partner_id.check_balance = 'out_of_balance'
#                 else:
#                     task.partner_id.check_balance = 'balanced'

    @api.depends('sale_line_id', 'timesheet_ids', 'timesheet_ids.unit_amount')
    def _compute_remaining_hours_so(self):

        timesheets = self.timesheet_ids.filtered(
            lambda t: t.task_id.sale_line_id in (t.so_line, t._origin.so_line) and t.so_line.remaining_hours_available)

        mapped_remaining_hours = {task._origin.id: task.sale_line_id and task.sale_line_id.remaining_hours or 0.0 for
                                  task in self}
        uom_hour = self.env.ref('uom.product_uom_hour')
        for timesheet in timesheets:
            delta = 0
            if timesheet._origin.so_line == timesheet.task_id.sale_line_id:
                delta += timesheet._origin.unit_amount
            if timesheet.so_line == timesheet.task_id.sale_line_id:
                delta -= timesheet.unit_amount
            if delta:
                mapped_remaining_hours[timesheet.task_id._origin.id] += timesheet.product_uom_id._compute_quantity(
                    delta, uom_hour)

        for task in self:
            if task.jobsheet_type == 'prepaid':
                task.remaining_hours_so = task.remaining_hours
            else:
                task.remaining_hours_so = mapped_remaining_hours[task._origin.id]
