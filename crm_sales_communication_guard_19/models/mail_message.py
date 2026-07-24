from odoo import api, models


class MailMessage(models.Model):
    _inherit = "mail.message"

    @api.model_create_multi
    def create(self, vals_list):
        messages = super().create(vals_list)
        if not self.env.context.get("skip_crm_sales_guard_recompute"):
            messages._process_crm_guard_events()
        return messages

    def write(self, vals):
        before_ids = self._related_crm_lead_ids()
        result = super().write(vals)
        if not self.env.context.get("skip_crm_sales_guard_recompute"):
            lead_ids = before_ids | self._related_crm_lead_ids()
            if lead_ids:
                self.env["crm.lead"].sudo().browse(list(lead_ids))._recompute_sales_communication_status()
        return result

    def unlink(self):
        lead_ids = self._related_crm_lead_ids()
        result = super().unlink()
        if lead_ids and not self.env.context.get("skip_crm_sales_guard_recompute"):
            self.env["crm.lead"].sudo().browse(list(lead_ids))._recompute_sales_communication_status()
        return result

    def _related_crm_lead_ids(self):
        return set(self.filtered(
            lambda message: message.model == "crm.lead" and message.res_id
        ).mapped("res_id"))

    def _crm_guard_internal_partner_ids(self):
        return set(
            self.env["res.users"]
            .sudo()
            .with_context(active_test=False)
            .search([("share", "=", False)])
            .mapped("partner_id")
            .ids
        )

    def _is_crm_internal_note(self, internal_partner_ids=None):
        """Return whether this message is an internal CRM note.

        Odoo normally uses ``mail.mt_note``, but inherited/custom chatter flows
        can use another subtype whose ``internal`` flag is true. Supporting both
        avoids silently missing notes while still excluding tracking messages.
        """
        self.ensure_one()
        internal_partner_ids = (
            internal_partner_ids
            if internal_partner_ids is not None
            else self._crm_guard_internal_partner_ids()
        )
        author_is_internal = bool(
            self.author_id and self.author_id.id in internal_partner_ids
        )
        if not author_is_internal or self.message_type != "comment":
            return False

        note_subtype = self.env.ref("mail.mt_note", raise_if_not_found=False)
        return bool(
            self.subtype_id
            and (
                (note_subtype and self.subtype_id.id == note_subtype.id)
                or self.subtype_id.internal
            )
        )

    def _process_crm_guard_events(self):
        crm_messages = self.filtered(
            lambda message: message.model == "crm.lead" and message.res_id
        )
        if not crm_messages:
            return True

        internal_partner_ids = crm_messages._crm_guard_internal_partner_ids()

        for message in crm_messages:
            lead = self.env["crm.lead"].sudo().browse(message.res_id).exists()
            if not lead:
                continue

            author_is_internal = bool(
                message.author_id and message.author_id.id in internal_partner_ids
            )
            if message._is_crm_internal_note(internal_partner_ids):
                lead._increment_user_unread(message, "internal_note")
            elif message.message_type == "email" and not author_is_internal:
                lead._increment_user_unread(message, "customer")

        lead_ids = crm_messages._related_crm_lead_ids()
        if lead_ids:
            self.env["crm.lead"].sudo().browse(list(lead_ids))._recompute_sales_communication_status()
        return True
