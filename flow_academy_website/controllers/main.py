from odoo import http,_
from odoo.http import request
from odoo.addons.website_event.controllers.main import WebsiteEventController
from odoo.addons.portal.controllers.web import Home

import logging
_logger = logging.getLogger(__name__)


class Website(Home):

    @http.route()
    def index(self, **kw):
        response = super(Website, self).index(**kw)
        website = request.website
        if website.id != 2:
            response.delete_cookie('logo_preference')
        return response


class WebsiteEventControllerInherit(WebsiteEventController):

    @http.route()
    def registration_confirm(self, event, **post):
        # 1. Call the super method to let Odoo handle the standard logic
        res = super(WebsiteEventControllerInherit, self).registration_confirm(event, **post)

        # 2. Re-evaluate the registration data to see if we are in the "Checkout" flow
        registrations = self._process_attendees_form(event, post)

        # 3. If there are tickets, check the order status
        if any(info.get('event_ticket_id') for info in registrations):
            order_sudo = request.website.sale_get_order()

            # CASE: Paid tickets (The original function redirects to /shop/checkout)
            if order_sudo and order_sudo.amount_total:
                # --- PASSING DATA VIA SESSION ---
                # We store a dictionary in the session.
                # Think of this as your "kwargs" for the next request.
                request.session['custom_checkout_data'] = {
                    'event_id': event.id,
                    'event_name': event.name,
                    'event_categ_id': event.event_category_id.id,
                    'attendee_count': len(registrations),
                    'my_custom_flag': True,
                    'original_post_data': post  # You can even pass the original post data
                }

                flow_temp = request.env['sale.order.template'].sudo().search([('is_flow_template','=', True)], limit=1)
                # 'self' is the current sale.order record
                order_sudo.write({
                    'sale_order_template_id': flow_temp and flow_temp.id or False,
                    # You could also change the salesperson, analytic account, etc.
                })

                # Explicitly return the redirect to ensure our session data is saved
                return request.redirect("/shop/checkout")

        # For free tickets or other cases, return the original result
        return res

    def _process_tickets_form(self, event, form_details):
        """ Process posted data about ticket order. Generic ticket are supported
        for event without tickets (generic registration).

        :return: list of order per ticket: [{
            'id': if of ticket if any (0 if no ticket),
            'ticket': browse record of ticket if any (None if no ticket),
            'name': ticket name (or generic 'Registration' name if no ticket),
            'quantity': number of registrations for that ticket,
        }, {...}]
        """
        ticket_order = {}
        for key, value in form_details.items():
            registration_items = key.split('nb_register-')
            if len(registration_items) != 2:
                continue
            ticket_order[int(registration_items[1])] = int(value)

        _logger.info(f"ticket_order >> {ticket_order}")

        ticket_dict = dict((ticket.id, ticket) for ticket in request.env['event.event.ticket'].sudo().search([
            ('id', 'in', [tid for tid in ticket_order.keys() if tid]),
            ('event_id', '=', event.id)
        ]))

        _logger.info(f"ticket_dict >> {ticket_dict}")
        data = []
        for tid, count in ticket_order.items():
            if ticket_dict.get(tid):
                data.append({
                    'id': tid if ticket_dict.get(tid) else 0,
                    'ticket': ticket_dict.get(tid),
                    'name': ticket_dict[tid]['name'] if ticket_dict.get(tid) else _('Registration'),
                    'quantity': count,
                    'price': ticket_dict[tid]['price']
                })

        _logger.info(f"data >> {data}")

        return data

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

        request.session['use_flow_logo'] = True


        # Return the template with the data
        response = request.render('flow_academy_website.events_by_category', {
            'events': events,
            'event_category': category,
        })

        response.set_cookie(
            'logo_preference',
            'flow_logo',  # or 'default_logo'
            max_age=30 * 24 * 60 * 60,  # 30 days in seconds
            httponly=False,  # Allow JavaScript to read it
            samesite='Lax'
        )

        return response

