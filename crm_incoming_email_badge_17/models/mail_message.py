from collections import defaultdict

from odoo import api, models


class MailMessage(models.Model):
    _inherit = "mail.message"

    @api.model_create_multi
    def create(self, vals_list):
        messages = super().create(vals_list)
        messages._update_crm_email_badges()
        return messages

    def _update_crm_email_badges(self):
        crm_messages = self.filtered(
            lambda message: (
                message.model == "crm.lead"
                and message.res_id
                and message.message_type in ("email", "comment")
            )
        )
        if not crm_messages:
            return

        internal_partner_ids = set(
            self.env["res.users"]
            .sudo()
            .search([
                ("share", "=", False),
                ("active", "in", [True, False]),
            ])
            .mapped("partner_id")
            .ids
        )

        updates_by_lead = defaultdict(list)
        for message in crm_messages.sorted(key=lambda msg: (msg.date, msg.id)):
            updates_by_lead[message.res_id].append(message)

        leads = self.env["crm.lead"].sudo().browse(updates_by_lead.keys()).exists()

        for lead in leads:
            values = {}
            waiting_count = lead.incoming_email_count
            status = lead.email_reply_status or "none"

            for message in updates_by_lead[lead.id]:
                author_is_internal = (
                    bool(message.author_id)
                    and message.author_id.id in internal_partner_ids
                )
                subtype_is_internal = bool(
                    message.subtype_id and message.subtype_id.internal
                )

                # Incoming customer email.
                if message.message_type == "email" and not author_is_internal:
                    waiting_count += 1
                    status = "waiting"
                    values["last_customer_email_date"] = message.date
                    continue

                # Public reply posted/sent by an internal Odoo user.
                # Internal notes do not mark the opportunity as replied.
                if author_is_internal and not subtype_is_internal:
                    waiting_count = 0
                    status = "replied"
                    values["last_internal_reply_date"] = message.date

            values.update({
                "incoming_email_count": waiting_count,
                "email_reply_status": status,
            })
            lead.write(values)
