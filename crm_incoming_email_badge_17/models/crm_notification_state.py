from psycopg2 import IntegrityError

from odoo import api, fields, models


class CrmLeadNotificationState(models.Model):
    _name = "crm.lead.notification.state"
    _description = "CRM Lead Per-user Notification State"
    _order = "write_date desc, id desc"
    _rec_name = "lead_id"

    lead_id = fields.Many2one(
        "crm.lead",
        required=True,
        index=True,
        ondelete="cascade",
    )
    user_id = fields.Many2one(
        "res.users",
        required=True,
        index=True,
        ondelete="cascade",
    )
    company_id = fields.Many2one(
        related="lead_id.company_id",
        store=True,
        index=True,
    )
    customer_unread_count = fields.Integer(default=0, required=True)
    internal_note_unread_count = fields.Integer(default=0, required=True)
    last_customer_message_id = fields.Many2one("mail.message", ondelete="set null")
    last_internal_note_id = fields.Many2one("mail.message", ondelete="set null")
    last_read_date = fields.Datetime()

    _sql_constraints = [
        (
            "crm_lead_notification_state_user_lead_unique",
            "unique(lead_id, user_id)",
            "A user can have only one notification state per CRM opportunity.",
        )
    ]

    @api.model
    def _get_or_create(self, lead, user):
        """Concurrency-safe getter used by mail gateway and bus event processing."""
        domain = [("lead_id", "=", lead.id), ("user_id", "=", user.id)]
        state = self.sudo().search(domain, limit=1)
        if state:
            return state
        try:
            with self.env.cr.savepoint():
                return self.sudo().create({"lead_id": lead.id, "user_id": user.id})
        except IntegrityError:
            return self.sudo().search(domain, limit=1)

    def increment_for_message(self, message, kind):
        """Increment once per message, protecting against duplicate event processing."""
        self.ensure_one()
        if kind == "customer":
            if self.last_customer_message_id == message:
                return False
            self.sudo().write({
                "customer_unread_count": self.customer_unread_count + 1,
                "last_customer_message_id": message.id,
            })
        elif kind == "internal_note":
            if self.last_internal_note_id == message:
                return False
            self.sudo().write({
                "internal_note_unread_count": self.internal_note_unread_count + 1,
                "last_internal_note_id": message.id,
            })
        else:
            return False
        return True

    def mark_read(self, customer=True, internal_notes=True):
        values = {"last_read_date": fields.Datetime.now()}
        if customer:
            values["customer_unread_count"] = 0
        if internal_notes:
            values["internal_note_unread_count"] = 0
        self.sudo().write(values)
        return True
