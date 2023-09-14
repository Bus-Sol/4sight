# -*- coding: utf-8 -*-
from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        if any(service for service in self.order_line if
               service.product_id.service_policy == 'ordered_timesheet' and service.product_id.is_jobsheets) and self.partner_id.jobsheet_type == 'prepaid':
            move = self._create_invoices()
            move.action_post()
            customer = move.partner_id
            for service in customer.service_ids:
                if service.product_id.product_variant_id.id in self.order_line.filtered(lambda line: line.product_id.is_jobsheets).mapped('product_id').ids:
                    service.extra_hour = service.quantity * (service.buffer / 100)
            self.env['client.jobsheet'].get_email_template_and_send(move)

        return res


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_jobsheets = fields.Boolean("Is Jobsheets")
