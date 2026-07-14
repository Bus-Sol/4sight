from collections import defaultdict


def post_init_hook(env):

    internal_partner_ids = set(
        env["res.users"]
        .sudo()
        .search([
            ("share", "=", False),
            ("active", "in", [True, False]),
        ])
        .mapped("partner_id")
        .ids
    )

    messages = env["mail.message"].sudo().search(
        [
            ("model", "=", "crm.lead"),
            ("res_id", "!=", 0),
            ("message_type", "in", ["email", "comment"]),
        ],
        order="res_id, date, id",
    )

    state_by_lead = defaultdict(
        lambda: {
            "incoming_email_count": 0,
            "email_reply_status": "none",
            "last_customer_email_date": False,
            "last_internal_reply_date": False,
        }
    )

    for message in messages:
        state = state_by_lead[message.res_id]

        author_is_internal = (
            bool(message.author_id)
            and message.author_id.id in internal_partner_ids
        )

        subtype_is_internal = bool(
            message.subtype_id and message.subtype_id.internal
        )

        # Customer email
        if message.message_type == "email" and not author_is_internal:
            state["incoming_email_count"] += 1
            state["email_reply_status"] = "waiting"
            state["last_customer_email_date"] = message.date
            continue

        # Internal public reply
        if author_is_internal and not subtype_is_internal:
            state["incoming_email_count"] = 0
            state["email_reply_status"] = "replied"
            state["last_internal_reply_date"] = message.date

    leads = env["crm.lead"].sudo().browse(list(state_by_lead.keys())).exists()

    for lead in leads:
        lead.write(state_by_lead[lead.id])
