import logging

from odoo import fields, models


_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    website_event_sale_notification_sent = fields.Boolean(
        copy=False,
        string="Website Event Sale Notification Sent",
    )

    def _compute_sale_order_template_id(self):
        Lead = self.env["crm.lead"]
        for order in self:
            if "website_id" in self._fields and order.website_id:
                continue

            lead = order.opportunity_id
            if not lead and self.env.context.get("default_opportunity_id"):
                lead = Lead.browse(self.env.context["default_opportunity_id"])

            if lead:
                order.sale_order_template_id = lead.team_id.sale_order_template_id.id or False
                continue

            super(SaleOrder, order)._compute_sale_order_template_id()

    def action_confirm(self):
        res = super().action_confirm()
        self._send_website_event_sale_order_notification()
        return res

    def _send_website_event_sale_order_notification(self):
        template = self.env.ref(
            "flow_academy_website.mail_template_website_event_sale_order_notification",
            raise_if_not_found=False,
        )
        group = self.env.ref(
            "flow_academy_website.group_website_event_sale_order_notification",
            raise_if_not_found=False,
        )
        if not template or not group:
            return

        partners = group.users.mapped("partner_id").filtered("email")
        email_to = ",".join(partners.mapped("email_formatted"))
        if not email_to:
            _logger.info("No recipients configured for website event sale order notifications.")
            return

        for order in self.filtered(lambda so: so._should_send_website_event_sale_order_notification()):
            template.sudo().send_mail(
                order.id,
                force_send=False,
                email_values={"email_to": email_to},
            )
            order.sudo().website_event_sale_notification_sent = True

    def _should_send_website_event_sale_order_notification(self):
        self.ensure_one()
        return (
            self.website_id
            and not self.website_event_sale_notification_sent
            and self.state in ("sale", "done")
            and any(self.order_line.mapped("event_ticket_id"))
        )
