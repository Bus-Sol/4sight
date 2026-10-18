from odoo import fields, models


class EventRegistrationAnswer(models.Model):
    _inherit = "event.registration.answer"

    attendee_name = fields.Char(related="registration_id.name", string="Attendee", store=False)
    event_date = fields.Datetime(related="event_id.date_begin", string="Event Date", store=False)
    answer_display = fields.Char(string="Answer", compute="_compute_answer_display")

    def _compute_answer_display(self):
        for answer in self:
            answer.answer_display = answer.value_answer_id.name or answer.value_text_box or False
