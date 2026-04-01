from odoo import fields, models


class CrmLead(models.Model):
    _inherit = "crm.lead"

    event_id = fields.Many2one("event.event", string="Event")
    attendees_qty = fields.Integer(string="Attendees Qty", default=1)

    def _prepare_opportunity_quotation_context(self):
        self.ensure_one()
        quotation_context = super()._prepare_opportunity_quotation_context()
        if self.event_id and self.attendees_qty > 0:
            ticket = self.event_id.event_ticket_ids.sorted(lambda t: (t.sequence, t.id))[:1]
            if ticket and ticket.product_id:
                quotation_context.setdefault("default_order_line", [])
                quotation_context["default_order_line"] = list(quotation_context["default_order_line"]) + [
                    (0, 0, {
                        "product_id": ticket.product_id.id,
                        "product_uom_qty": self.attendees_qty,
                        "event_id": self.event_id.id,
                        "event_ticket_id": ticket.id,
                    })
                ]
        return quotation_context
