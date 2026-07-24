from collections import defaultdict

from odoo import api, fields, models, _


class CrmLead(models.Model):
    _inherit = "crm.lead"

    incoming_email_count = fields.Integer(
        string="Customer Messages Waiting",
        default=0,
        copy=False,
        readonly=True,
        help="External customer emails received since the latest internal public reply.",
    )
    email_reply_status = fields.Selection(
        selection=[
            ("none", "No Email Activity"),
            ("waiting", "Waiting for Reply"),
            ("replied", "Replied"),
        ],
        string="Customer Reply Status",
        default="none",
        copy=False,
        readonly=True,
        index=True,
    )
    last_customer_email_date = fields.Datetime(
        string="Last Customer Email", copy=False, readonly=True, index=True
    )
    last_internal_reply_date = fields.Datetime(
        string="Last Public Reply", copy=False, readonly=True, index=True
    )
    internal_note_count = fields.Integer(
        string="Internal Notes", default=0, copy=False, readonly=True
    )
    last_internal_note_date = fields.Datetime(
        string="Last Internal Note", copy=False, readonly=True, index=True
    )
    last_internal_note_author_id = fields.Many2one(
        "res.users", string="Last Internal Note By", copy=False, readonly=True
    )

    notification_state_ids = fields.One2many(
        "crm.lead.notification.state", "lead_id", string="User Notification States"
    )
    my_customer_unread_count = fields.Integer(
        string="My Unread Customer Messages",
        compute="_compute_my_notification_state",
        search="_search_my_customer_unread_count",
    )
    my_internal_note_unread_count = fields.Integer(
        string="My Unread Internal Notes",
        compute="_compute_my_notification_state",
        search="_search_my_internal_note_unread_count",
    )
    my_total_unread_count = fields.Integer(
        string="My Total Unread", compute="_compute_my_notification_state"
    )

    sales_followup_status = fields.Selection(
        selection=[
            ("none", "No Next Activity"),
            ("planned", "Activity Planned"),
            ("today", "Due Today"),
            ("overdue", "Activity Overdue"),
        ],
        compute="_compute_sales_followup_status",
        store=True,
        index=True,
    )
    sales_attention_status = fields.Selection(
        selection=[
            ("normal", "Normal"),
            ("customer_waiting", "Customer Waiting"),
            ("activity_overdue", "Activity Overdue"),
            ("no_next_action", "No Next Action"),
        ],
        compute="_compute_sales_attention_status",
        store=True,
        index=True,
    )
    sales_attention_reason = fields.Char(
        compute="_compute_sales_attention_status", store=True
    )

    # Kanban templates deliberately use only these simple booleans.
    show_customer_waiting_badge = fields.Boolean(compute="_compute_badge_flags")
    show_customer_replied_badge = fields.Boolean(compute="_compute_badge_flags")
    show_overdue_activity_badge = fields.Boolean(compute="_compute_badge_flags")
    show_no_next_activity_badge = fields.Boolean(compute="_compute_badge_flags")

    @api.depends_context("uid")
    def _compute_my_notification_state(self):
        counts = {}
        persisted = self.filtered("id")
        if persisted:
            states = self.env["crm.lead.notification.state"].sudo().search([
                ("lead_id", "in", persisted.ids),
                ("user_id", "=", self.env.user.id),
            ])
            counts = {
                state.lead_id.id: (
                    state.customer_unread_count,
                    state.internal_note_unread_count,
                )
                for state in states
            }
        for lead in self:
            customer, notes = counts.get(lead.id, (0, 0))
            lead.my_customer_unread_count = customer
            lead.my_internal_note_unread_count = notes
            lead.my_total_unread_count = customer + notes

    @api.model
    def _search_my_customer_unread_count(self, operator, value):
        return self._search_my_unread_field("customer_unread_count", operator, value)

    @api.model
    def _search_my_internal_note_unread_count(self, operator, value):
        return self._search_my_unread_field("internal_note_unread_count", operator, value)

    @api.model
    def _search_my_unread_field(self, field_name, operator, value):
        states = self.env["crm.lead.notification.state"].sudo().search([
            ("user_id", "=", self.env.user.id),
            (field_name, operator, value),
        ])
        return [("id", "in", states.mapped("lead_id").ids)]

    @api.depends("activity_ids.date_deadline", "activity_ids.active")
    def _compute_sales_followup_status(self):
        today = fields.Date.context_today(self)
        for lead in self:
            activities = lead.activity_ids.filtered("active")
            deadlines = [deadline for deadline in activities.mapped("date_deadline") if deadline]
            if not deadlines:
                lead.sales_followup_status = "none"
            elif any(deadline < today for deadline in deadlines):
                lead.sales_followup_status = "overdue"
            elif any(deadline == today for deadline in deadlines):
                lead.sales_followup_status = "today"
            else:
                lead.sales_followup_status = "planned"

    @api.depends("active", "won_status", "email_reply_status", "sales_followup_status")
    def _compute_sales_attention_status(self):
        for lead in self:
            if not lead.active or lead.won_status == "won":
                status, reason = "normal", False
            elif lead.email_reply_status == "waiting":
                status, reason = "customer_waiting", _("Customer email is waiting for a reply")
            elif lead.sales_followup_status == "overdue":
                status, reason = "activity_overdue", _("A sales activity is overdue")
            elif lead.sales_followup_status == "none":
                status, reason = "no_next_action", _("No next sales activity is scheduled")
            else:
                status, reason = "normal", False
            lead.sales_attention_status = status
            lead.sales_attention_reason = reason

    @api.depends_context("uid")
    @api.depends(
        "email_reply_status",
        "sales_followup_status",
    )
    def _compute_badge_flags(self):
        for lead in self:
            lead.show_customer_waiting_badge = lead.email_reply_status == "waiting"
            lead.show_customer_replied_badge = lead.email_reply_status == "replied"
            lead.show_overdue_activity_badge = (
                lead.email_reply_status != "waiting"
                and lead.sales_followup_status == "overdue"
            )
            lead.show_no_next_activity_badge = (
                lead.email_reply_status != "waiting"
                and lead.sales_followup_status == "none"
            )


    def message_post(self, **kwargs):
        """Safety net for CRM chatter events.

        ``mail.message.create`` remains the primary hook. Calling the processor
        here as well covers customized chatter implementations that bypass or
        defer the generic create hook. Duplicate unread increments are blocked
        by the per-user state model's last-message checks.
        """
        message = super().message_post(**kwargs)
        if (
            message
            and not self.env.context.get("skip_crm_sales_guard_recompute")
        ):
            message._process_crm_guard_events()
        return message

    def _notification_recipient_users(self):
        """Return internal users who should receive CRM communication alerts.

        Recipients include the assigned salesperson, sales-team leader, team
        members, and active internal followers. The message author is excluded
        later when the unread event is processed.
        """
        self.ensure_one()
        users = self.env["res.users"].sudo().browse()

        if self.user_id and self.user_id.active and not self.user_id.share:
            users |= self.user_id

        if self.team_id:
            if (
                self.team_id.user_id
                and self.team_id.user_id.active
                and not self.team_id.user_id.share
            ):
                users |= self.team_id.user_id
            if "member_ids" in self.team_id._fields:
                users |= self.team_id.member_ids.filtered(
                    lambda user: user.active and not user.share
                )

        if self.message_partner_ids:
            users |= self.env["res.users"].sudo().search([
                ("partner_id", "in", self.message_partner_ids.ids),
                ("share", "=", False),
                ("active", "=", True),
            ])

        if self.company_id:
            users = users.filtered(lambda user: self.company_id in user.company_ids)
        return users

    def _increment_user_unread(self, message, kind):
        self.ensure_one()
        author_users = message.author_id.user_ids.filtered(
            lambda user: user.active and not user.share
        )
        recipients = self._notification_recipient_users() - author_users
        state_model = self.env["crm.lead.notification.state"]

        for user in recipients:
            state = state_model._get_or_create(self, user)
            if not state.increment_for_message(message, kind):
                continue

            if kind == "customer":
                title = _("New customer message")
                body = _("%(lead)s has a new customer email.", lead=self.display_name)
                notification_type = "warning"
            else:
                title = _("New CRM internal note")
                body = _("A new internal note was added to %(lead)s.", lead=self.display_name)
                notification_type = "info"

            self.env["bus.bus"]._sendone(
                user.partner_id,
                "crm_sales_guard_notification",
                {
                    "title": title,
                    "message": body,
                    "type": notification_type,
                    "lead_id": self.id,
                    "lead_name": self.display_name,
                    "action_url": "/web#id=%s&model=crm.lead&view_type=form" % self.id,
                    "customer_unread_count": state.customer_unread_count,
                    "internal_note_unread_count": state.internal_note_unread_count,
                },
            )

    def action_mark_communication_read(self):
        states = self.env["crm.lead.notification.state"].sudo().search([
            ("lead_id", "in", self.ids),
            ("user_id", "=", self.env.user.id),
        ])
        states.mark_read()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("CRM Communication"),
                "message": _("Your CRM communication was marked as read."),
                "type": "success",
                "sticky": False,
                "next": {"type": "ir.actions.client", "tag": "reload"},
            },
        }

    def action_recalculate_sales_communication(self):
        self._recompute_sales_communication_status()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("CRM Communication"),
                "message": _("Communication status recalculated for %s record(s).", len(self)),
                "type": "success",
                "sticky": False,
                "next": {"type": "ir.actions.client", "tag": "reload"},
            },
        }

    def _recompute_sales_communication_status(self):
        """Rebuild global status from chatter; safe after imports, edits and deletions."""
        leads = self.sudo().exists()
        if not leads:
            return True

        internal_users = self.env["res.users"].sudo().with_context(active_test=False).search([
            ("share", "=", False),
        ])
        internal_partner_ids = set(internal_users.mapped("partner_id").ids)
        user_by_partner = {
            user.partner_id.id: user.id for user in internal_users if user.partner_id
        }
        messages = self.env["mail.message"].sudo().search([
            ("model", "=", "crm.lead"),
            ("res_id", "in", leads.ids),
            ("message_type", "in", ["email", "comment"]),
        ], order="res_id, date, id")

        values_by_lead = defaultdict(lambda: {
            "incoming_email_count": 0,
            "email_reply_status": "none",
            "last_customer_email_date": False,
            "last_internal_reply_date": False,
            "internal_note_count": 0,
            "last_internal_note_date": False,
            "last_internal_note_author_id": False,
        })

        for message in messages:
            values = values_by_lead[message.res_id]
            author_partner_id = message.author_id.id if message.author_id else False
            author_is_internal = author_partner_id in internal_partner_ids
            is_internal_note = message._is_crm_internal_note(internal_partner_ids)

            if is_internal_note:
                values["internal_note_count"] += 1
                values["last_internal_note_date"] = message.date
                values["last_internal_note_author_id"] = user_by_partner.get(author_partner_id)
            elif message.message_type == "email" and not author_is_internal:
                values["incoming_email_count"] += 1
                values["email_reply_status"] = "waiting"
                values["last_customer_email_date"] = message.date
            elif author_is_internal and not is_internal_note:
                values["incoming_email_count"] = 0
                values["email_reply_status"] = "replied"
                values["last_internal_reply_date"] = message.date

        for lead in leads:
            lead.with_context(
                tracking_disable=True,
                mail_notrack=True,
                skip_crm_sales_guard_recompute=True,
            ).write(values_by_lead[lead.id])
        return True
