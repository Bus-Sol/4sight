from odoo import models


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    def _notify_compute_recipients(self, message, msg_vals):

        recipient_data = super()._notify_compute_recipients(message, msg_vals)
        if "notify_followers" in self.env.context:
            # filter out all the followers
            pids = (
                msg_vals.get("partner_ids", [])
                if msg_vals
                else message.sudo().partner_ids.ids
            )
            recipient_data = {
                "partners": [d for d in recipient_data["partners"] if d["id"] in pids],
                "channels": [],
            }
        return recipient_data