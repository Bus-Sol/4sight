from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestCrmSalesGuard(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.salesperson = cls.env["res.users"].with_context(no_reset_password=True).create({
            "name": "CRM Guard Salesperson",
            "login": "crm.guard.salesperson@example.com",
            "email": "crm.guard.salesperson@example.com",
            "groups_id": [(6, 0, [cls.env.ref("sales_team.group_sale_salesman").id])],
        })
        cls.customer = cls.env["res.partner"].create({
            "name": "CRM Guard Customer",
            "email": "customer@example.com",
        })
        cls.lead = cls.env["crm.lead"].create({
            "name": "CRM Guard Test Opportunity",
            "type": "opportunity",
            "partner_id": cls.customer.id,
            "user_id": cls.salesperson.id,
        })

    def test_customer_email_sets_waiting_and_unread(self):
        message = self.env["mail.message"].create({
            "model": "crm.lead",
            "res_id": self.lead.id,
            "message_type": "email",
            "subject": "Customer reply",
            "body": "Please send more information.",
            "author_id": self.customer.id,
        })
        self.assertTrue(message)
        self.lead.invalidate_recordset()
        self.assertEqual(self.lead.email_reply_status, "waiting")
        self.assertEqual(self.lead.incoming_email_count, 1)
        state = self.env["crm.lead.notification.state"].sudo().search([
            ("lead_id", "=", self.lead.id),
            ("user_id", "=", self.salesperson.id),
        ])
        self.assertEqual(state.customer_unread_count, 1)

    def test_internal_note_does_not_clear_customer_waiting(self):
        self.env["mail.message"].create({
            "model": "crm.lead",
            "res_id": self.lead.id,
            "message_type": "email",
            "body": "Customer message",
            "author_id": self.customer.id,
        })
        self.lead.with_user(self.salesperson).message_post(
            body="Internal follow-up required",
            subtype_xmlid="mail.mt_note",
        )
        self.lead.invalidate_recordset()
        self.assertEqual(self.lead.email_reply_status, "waiting")
        self.assertEqual(self.lead.internal_note_count, 1)

    def test_public_reply_clears_waiting_counter(self):
        self.env["mail.message"].create({
            "model": "crm.lead",
            "res_id": self.lead.id,
            "message_type": "email",
            "body": "Customer message",
            "author_id": self.customer.id,
        })
        self.lead.with_user(self.salesperson).message_post(
            body="Public response",
            subtype_xmlid="mail.mt_comment",
            message_type="comment",
        )
        self.lead.invalidate_recordset()
        self.assertEqual(self.lead.email_reply_status, "replied")
        self.assertEqual(self.lead.incoming_email_count, 0)

    def test_mark_read_is_per_user(self):
        state = self.env["crm.lead.notification.state"].sudo().create({
            "lead_id": self.lead.id,
            "user_id": self.salesperson.id,
            "customer_unread_count": 2,
            "internal_note_unread_count": 1,
        })
        self.lead.with_user(self.salesperson).action_mark_communication_read()
        state.invalidate_recordset()
        self.assertEqual(state.customer_unread_count, 0)
        self.assertEqual(state.internal_note_unread_count, 0)
