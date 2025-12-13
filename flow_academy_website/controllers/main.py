from odoo import http
from odoo.http import request


class EventTypeController(http.Controller):

    # This route accepts the custom type ID dynamically
    # Example URL: /events/type/1 (where 1 is the ID of the type)
    @http.route('/events/type/<model("event.category"):category>', type='http', auth="public", website=True)
    def list_events_by_type(self, category, **kw):
        # Search for events linked to this specific type
        # We also filter for 'published' events so website visitors don't see drafts
        events = request.env['event.event'].search([
            ('event_category_id', '=', category.id),
            ('website_published', '=', True)
        ])

        # Return the template with the data
        return request.render('flow_academy_website.events_by_category', {
            'events': events,
            'event_category': category,
        })


class EventRegistrationController(http.Controller):

    @http.route('/event/get_registration_form/<int:event_id>', type='http', auth="public", website=True)
    def get_registration_form(self, event_id, **kwargs):
        """Return the registration form modal for a specific event."""
        event = request.env['event.event'].browse(event_id).sudo()

        if not event.exists():
            return request.not_found()

        # Pass the specific event to the template
        values = {
            'event': event,
            'registration_error_code': kwargs.get('registration_error_code', False),
        }

        # Render just the modal content (not the entire page)
        return request.render('your_module.modal_ticket_registration_content', values)