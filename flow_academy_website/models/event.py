from odoo import api, fields, models
from odoo.exceptions import MissingError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class Event(models.Model):
    _inherit = "event.event"

    event_category_id = fields.Many2one(comodel_name="event.category", string="Event Category")

    price = fields.Monetary(string="price",  currency_field='currency_id', compute="compute_price")

    start_time = fields.Float(string="Start time")
    end_time = fields.Float(string="End time")

    trainer = fields.Char(string="Trainer")
    location_type = fields.Selection(string="Location", selection=[('ON Site', 'On-site'), ('Online', 'Online'), ])

    @api.depends('event_ticket_ids', 'event_ticket_ids.price')
    def compute_price(self):
        for rec in self:
            rec.price = max(rec.event_ticket_ids.mapped('price')) if rec.event_ticket_ids else 0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # If company_ids not provided, default to current company
            if not vals.get('website_published'):
                vals['website_published'] = True
        return super().create(vals_list)


class EventType(models.Model):
    _inherit = 'event.type'

    def _default_event_mail_type_ids(self):
        return [(0, 0,
                 {'notification_type': 'mail',
                  'interval_nbr': 0,
                  'interval_unit': 'now',
                  'interval_type': 'after_sub',
                  'template_ref': 'mail.template, %i' % self.env.ref('flow_academy_website.flow_event_subscription').id,
                 }),
                (0, 0,
                 {'notification_type': 'mail',
                  'interval_nbr': 1,
                  'interval_unit': 'hours',
                  'interval_type': 'before_event',
                  'template_ref': 'mail.template, %i' % self.env.ref('event.event_reminder').id,
                 }),
                (0, 0,
                 {'notification_type': 'mail',
                  'interval_nbr': 3,
                  'interval_unit': 'days',
                  'interval_type': 'before_event',
                  'template_ref': 'mail.template, %i' % self.env.ref('event.event_reminder').id,
                 })]


class EventMailRegistration(models.Model):
    _inherit = 'event.mail.registration'

    def execute(self):
        # add force_send param
        now = fields.Datetime.now()
        todo = self.filtered(lambda reg_mail:
            not reg_mail.mail_sent and \
            reg_mail.registration_id.state in ['open', 'done'] and \
            (reg_mail.scheduled_date and reg_mail.scheduled_date <= now) and \
            reg_mail.scheduler_id.notification_type == 'mail'
        )
        done = self.browse()
        for reg_mail in todo:
            organizer = reg_mail.scheduler_id.event_id.organizer_id
            company = self.env.company
            author = self.env.ref('base.user_root').partner_id
            if organizer.email:
                author = organizer
            elif company.email:
                author = company.partner_id
            elif self.env.user.email:
                author = self.env.user.partner_id

            email_values = {
                'author_id': author.id,
            }
            template = None
            try:
                template = reg_mail.scheduler_id.template_ref.exists()
            except MissingError:
                pass

            if not template:
                _logger.warning("Cannot process ticket %s, because Mail Scheduler %s has reference to non-existent template", reg_mail.registration_id, reg_mail.scheduler_id)
                continue

            if not template.email_from:
                email_values['email_from'] = author.email_formatted
            template.send_mail(reg_mail.registration_id.id, email_values=email_values, force_send=True)
            done |= reg_mail
        done.write({'mail_sent': True})