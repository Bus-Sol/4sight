# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class JobsheetInvoice(models.Model):
    _name = "jobsheet.invoice"
    _description = "create Invoice from multiple Jobsheets"

    @api.model
    def _count(self):
        return len(self._context.get('active_ids', []))

    count = fields.Integer(default=_count, string='Jobsheet Count')

    def create_invoices(self):
        jobsheets = self.env['client.jobsheet'].browse(self._context.get('active_ids', []))
        result = len(jobsheets.mapped('partner_id')) == 1
        if not result:
            raise UserError(_("Please select Jobsheets per one customer."))
        for jobsheet in jobsheets:
            if jobsheet.type == 'prepaid':
                raise UserError(_("You can only invoice Postpaid Type."))
        invoice_vals_list = []
        customer_ref = ' '.join(label for label in jobsheets.mapped('name') if label)
        invoice_vals = []
        if any(jobsheets.mapped('jobsheet_line').filtered(lambda line: line.product_id.is_Jobsheets) or
               jobsheets.filtered(lambda order: order.service_id.is_Jobsheets)):
            invoice_vals = jobsheets._prepare_invoice(ref=customer_ref)
        for order in jobsheets:
            if order.status == 'created' and order.company_id.inv_after_sign:
                raise UserError(_("Only signed jobsheets are ready to be invoiced."))
            if order.status == 'invoiced':
                raise UserError(_("Some jobsheets are already invoiced."))
            if order.service_id.is_Jobsheets:
                invoice_vals['invoice_line_ids'].append((0, 0, order._prepare_account_move_line_from_rate()))
            for line in order.jobsheet_line:
                if line.product_id.is_Jobsheets:
                    invoice_vals['invoice_line_ids'].append((0, 0, line._prepare_account_move_line()))
        # invoice_vals_list.append(invoice_vals)
        AccountMove = self.env['account.move'].with_context(default_move_type='out_invoice')
        if invoice_vals:
            moves = AccountMove.create(invoice_vals)
            for order in jobsheets:
                order.status = 'invoiced'
            if self._context.get('open_invoices', False):
                return jobsheets.action_open_invoice(moves)
