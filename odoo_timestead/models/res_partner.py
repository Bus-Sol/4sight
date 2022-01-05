# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    monthly_hours = fields.Float(string='Monthly Hours', digits='Product Unit of Measure')
    product_id = fields.Many2one('product.template', string='Service', domain=[('type','=', 'service'),('service_tracking', '!=', 'no')])
    type = fields.Selection(selection_add=[('jobsheet', 'Jobsheet Address')])
    receive_jobsheet = fields.Boolean('Receive Jobsheet')
    receive_invoice = fields.Boolean('Receive Invoice')
    service_ids = fields.Many2many('jobsheet.service', 'partner_jobsheet_service_rel',string='Related services')
    jobsheet_type = fields.Selection([('prepaid','Prepaid'),('contract_postpaid','Contract/Postpaid')])

    def write(self, vals):
        res = super(ResPartner, self).write(vals)
        print(res, vals)
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