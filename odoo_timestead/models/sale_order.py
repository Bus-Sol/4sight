# -*- coding: utf-8 -*-
from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        if any(service for service in self.order_line if service.product_id.service_policy =='ordered_timesheet') and self.partner_id.jobsheet_type == 'prepaid':
            move = self._create_invoices()
            move.action_post()
            customer = move.partner_id
            for service in customer.service_ids:
                if service.product_id.product_variant_id.id in self.order_line.mapped('product_id').ids:
                    service.extra_hour = service.quantity * (service.buffer / 100)
            self.env['client.jobsheet'].get_email_template_and_send(move)

        return res

    _sql_constraints = [
        # ('sale_subscription_state_coherence',
        #  "CHECK(NOT (is_subscription=TRUE AND state = 'sale' AND subscription_state='1_draft'))",
        #  "You cannot set to draft a confirmed subscription. Please create a new quotation"),
        # ('check_start_date_lower_next_invoice_date', 'CHECK((next_invoice_date IS NULL OR start_date IS NULL) OR (next_invoice_date >= start_date))',
        #  'The next invoice date of a sale order should be after its start date.'),
    ]

    def _send_order_confirmation_mail(self):
        """ Send a mail to the SO customer to inform them that their order has been confirmed.

        :return: None
        """
        for order in self:
            mail_template = order._get_confirmation_template()
            # order._send_order_notification_mail(mail_template)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _compute_price_unit(self):
        lines_without_price_recomputation = self.filtered(lambda l: l.product_id and l.create_date)
        super(SaleOrderLine, self - lines_without_price_recomputation)._compute_price_unit()