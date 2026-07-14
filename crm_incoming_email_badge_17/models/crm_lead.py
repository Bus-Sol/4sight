from odoo import fields, models


class CrmLead(models.Model):
    _inherit = "crm.lead"

    incoming_email_count = fields.Integer(
        string="Incoming Emails Waiting",
        default=0,
        copy=False,
        readonly=True,
        help="Number of external incoming emails received since the latest internal public reply.",
    )

    email_reply_status = fields.Selection(
        selection=[
            ("none", "No Email Activity"),
            ("waiting", "Waiting for Reply"),
            ("replied", "Replied"),
        ],
        string="Email Reply Status",
        default="none",
        copy=False,
        readonly=True,
        index=True,
    )

    last_customer_email_date = fields.Datetime(
        string="Last Customer Email",
        copy=False,
        readonly=True,
        index=True,
    )

    last_internal_reply_date = fields.Datetime(
        string="Last Internal Reply",
        copy=False,
        readonly=True,
        index=True,
    )
