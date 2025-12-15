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

