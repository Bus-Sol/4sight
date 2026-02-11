from odoo import http,_
from odoo.http import request
from odoo.addons.website_event.controllers.main import WebsiteEventController
from odoo.addons.portal.controllers.web import Home
from odoo.addons.sale.controllers.portal import CustomerPortal
from datetime import datetime,date
import logging
_logger = logging.getLogger(__name__)


class CustomerPortalExternalTax(CustomerPortal):


    @http.route()
    def portal_order_page(self, *args, **kwargs):
        response = super().portal_order_page(*args, **kwargs)
        if 'sale_order' not in response.qcontext:
            return response

        so = response.qcontext['sale_order']
        website = request.website

        flow_temp = request.env['sale.order.template'].sudo().search([('is_flow_template', '=', True)], limit=1)
        # 'self' is the current sale.order record
        if so.sale_order_template_id.id == flow_temp.id:
            response.set_cookie(
                'logo_preference',
                'flow_logo',  # or 'default_logo'
                max_age=24 * 60 * 60,
                httponly=False,  # Allow JavaScript to read it
                samesite='Lax'
            )
        else:
            response.delete_cookie('logo_preference')
        return response


    @http.route()
    def portal_my_invoice_detail(self, *args, **kw):
        response = super().portal_my_invoice_detail(*args, **kw)
        if 'invoice' not in response.qcontext:
            return response

        invoice = response.qcontext['invoice']
        flow_temp = request.env['sale.order.template'].sudo().search([('is_flow_template', '=', True)], limit=1)
        # 'self' is the current sale.order record
        if invoice.sale_order_template_id.id == flow_temp.id:
            response.set_cookie(
                'logo_preference',
                'flow_logo',  # or 'default_logo'
                max_age=24 * 60 * 60,
                httponly=False,  # Allow JavaScript to read it
                samesite='Lax'
            )
        else:
            response.delete_cookie('logo_preference')
        return response




class Website(Home):

    @http.route()
    def index(self, **kw):
        response = super(Website, self).index(**kw)
        website = request.website
        if website.id != 2:
            response.delete_cookie('logo_preference')
        else:
            response.set_cookie(
                'logo_preference',
                'flow_logo',  # or 'default_logo'
                max_age= 24 * 60 * 60,
                httponly=False,  # Allow JavaScript to read it
                samesite='Lax'
            )
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
        company_1 = request.env['res.company'].sudo().browse(1)

        now = datetime.now()

        events = request.env['event.event'].sudo().with_company(company_1).search([
            ('event_category_id', '=', category.id),
            ('date_begin', '>=', now),
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
            max_age=24 * 60 * 60,  # 30 days in seconds
            httponly=False,  # Allow JavaScript to read it
            samesite='Lax'
        )

        return response

    @http.route('/new-upcoming-courses', type='http', auth="public", website=True)
    def get_upcoming_courses(self, **kw):
        # Switch to company 1 context
        company_1 = request.env['res.company'].sudo().browse(1)

        event_categs = request.env['event.category'].sudo().with_company(company_1).search([])
        now = datetime.now()
        categs_data = {}

        for categ in event_categs:
            categs_data[categ.id] = []
            events = request.env['event.event'].sudo().with_company(company_1).search([
                ('company_id', '=', 1),
                ('event_category_id', '=', categ.id),
                ('date_begin', '>=', now),
            ])
            for event in events:
                categs_data[categ.id].append(event)

        _logger.info(f"categs_data >> {categs_data}")

        return (request.render('website.upcoming-courses_e0fcf3', {
            'categs_data': categs_data,
        }))

    # Individual Pages

    @http.route('/courses-2026', type='http', auth="public", website=True)
    def get_upcoming_courses_1(self, **kw):
        # Switch to company 1 context
        company_1 = request.env['res.company'].sudo().browse(1)
        now = datetime.now()

        events = request.env['event.event'].sudo().with_company(company_1).search([
            ('event_category_id', '=', 1),
            ('date_begin', '>=', now),
        ])

        _logger.info(f"categ 1 events >> {events}")

        return request.render('website.practical-ai-for-the-workplace', {
            'events': events,
        })

    @http.route('/seo-for-marketers-2026', type='http', auth="public", website=True)
    def get_upcoming_courses_2(self, **kw):
        # Switch to company 1 context
        company_1 = request.env['res.company'].sudo().browse(1)
        now = datetime.now()

        seo_events = request.env['event.event'].sudo().with_company(company_1).search([
            ('event_category_id', '=', 2),
            ('date_begin', '>=', now),
        ])

        _logger.info(f"seo_events >> {seo_events}")

        return request.render('website.ai-for-work-1_e38eb1', {
            'seo_events': seo_events,
        })

    @http.route('/master-canva-for-social-media-2026', type='http', auth="public", website=True)
    def get_upcoming_courses_3(self, **kw):
        # Switch to company 1 context
        company_1 = request.env['res.company'].sudo().browse(1)
        now = datetime.now()

        events = request.env['event.event'].sudo().with_company(company_1).search([
            ('event_category_id', '=', 3),
            ('date_begin', '>=', now),
        ])

        _logger.info(f"categ 3 events >> {events}")

        return request.render('website.ai-for-work-1_ef4c18', {
            'events': events,
        })

    @http.route('/ai-for-business-administrators-personal-assistants', type='http', auth="public", website=True)
    def get_upcoming_courses_4(self, **kw):
        # Switch to company 1 context
        company_1 = request.env['res.company'].sudo().browse(1)
        now = datetime.now()

        ai_events = request.env['event.event'].sudo().with_company(company_1).search([
            ('event_category_id', '=', 4),
            ('date_begin', '>=', now),
        ])

        _logger.info(f"ai_events >> {ai_events}")

        return request.render('website.ai-for-work-1_1b3066', {
            'ai_events': ai_events,
        })

    @http.route('/blockchain-and-distributed-ledger-technologies', type='http', auth="public", website=True)
    def get_upcoming_courses_5(self, **kw):
        # Switch to company 1 context
        company_1 = request.env['res.company'].sudo().browse(1)
        now = datetime.now()

        events = request.env['event.event'].sudo().with_company(company_1).search([
            ('event_category_id', '=', 5),
            ('date_begin', '>=', now),
        ])

        _logger.info(f"categ 5 events >> {events}")

        return request.render('website.ai-for-work-1_56f972', {
            'events': events,
        })


    @http.route('/transformative-leadership-programme', type='http', auth="public", website=True)
    def get_upcoming_courses_6(self, **kw):
        # Switch to company 1 context
        company_1 = request.env['res.company'].sudo().browse(1)
        now = datetime.now()

        events = request.env['event.event'].sudo().with_company(company_1).search([
            ('event_category_id', '=', 6),
            ('date_begin', '>=', now),
        ])

        _logger.info(f"categ 6 events >> {events}")

        return request.render('website.ai-for-work-1_3efddc', {
            'events': events,
        })

    @http.route('/public-speaking-foundations', type='http', auth="public", website=True)
    def get_upcoming_courses_7(self, **kw):
        # Switch to company 1 context
        company_1 = request.env['res.company'].sudo().browse(1)
        now = datetime.now()

        events = request.env['event.event'].sudo().with_company(company_1).search([
            ('event_category_id', '=', 7),
            ('date_begin', '>=', now),
        ])

        _logger.info(f"categ 7 events >> {events}")

        return request.render('website.ai-for-work-1_6fed98', {
            'events': events,
        })



    @http.route('/content-writing-foundations', type='http', auth="public", website=True)
    def get_upcoming_courses_8(self, **kw):
        # Switch to company 1 context
        company_1 = request.env['res.company'].sudo().browse(1)
        now = datetime.now()

        events = request.env['event.event'].sudo().with_company(company_1).search([
            ('event_category_id', '=', 8),
            ('date_begin', '>=', now),
        ])

        _logger.info(f"categ 8 events >> {events}")

        return request.render('website.ai-for-work-1_96645e', {
            'events': events,
        })


    @http.route('/foundations-in-ai-marketing', type='http', auth="public", website=True)
    def get_upcoming_courses_9(self, **kw):
        # Switch to company 1 context
        company_1 = request.env['res.company'].sudo().browse(1)
        now = datetime.now()

        events = request.env['event.event'].sudo().with_company(company_1).search([
            ('event_category_id', '=', 9),
            ('date_begin', '>=', now),
        ])

        _logger.info(f"categ 9 events >> {events}")

        return request.render('website.ai-for-work-1_1b3066_16c2f0', {
            'events': events,
        })

    @http.route('/sales-accelerator-foundations', type='http', auth="public", website=True)
    def get_upcoming_courses_10(self, **kw):
        # Switch to company 1 context
        company_1 = request.env['res.company'].sudo().browse(1)
        now = datetime.now()

        events = request.env['event.event'].sudo().with_company(company_1).search([
            ('event_category_id', '=', 10),
            ('date_begin', '>=', now),
        ])

        _logger.info(f"categ 1 events >> {events}")

        return request.render('website.ai-for-work-1_1b3066_355d9b', {
            'events': events,
        })

    @http.route('/strategic-sales-management-foundations', type='http', auth="public", website=True)
    def get_upcoming_courses_11(self, **kw):
        # Switch to company 1 context
        company_1 = request.env['res.company'].sudo().browse(1)
        now = datetime.now()

        events = request.env['event.event'].sudo().with_company(company_1).search([
            ('event_category_id', '=', 11),
            ('date_begin', '>=', now),
        ])

        _logger.info(f"categ 11 events >> {events}")

        return request.render('website.ai-for-work-1_1b3066_355d9b_e2c965', {
            'events': events,
        })

    @http.route('/project-management-fundamentals', type='http', auth="public", website=True)
    def get_upcoming_courses_12(self, **kw):
        # Switch to company 1 context
        company_1 = request.env['res.company'].sudo().browse(1)
        now = datetime.now()

        events = request.env['event.event'].sudo().with_company(company_1).search([
            ('event_category_id', '=', 12),
            ('date_begin', '>=', now),
        ])

        _logger.info(f"categ 12 events >> {events}")

        return request.render('website.ai-for-work-1_1b3066_13c129_7dfdcb_26adac', {
            'events': events,
        })

    @http.route('/foundations-of-agile-at-scale', type='http', auth="public", website=True)
    def get_upcoming_courses_13(self, **kw):
        # Switch to company 1 context
        company_1 = request.env['res.company'].sudo().browse(1)
        now = datetime.now()

        events = request.env['event.event'].sudo().with_company(company_1).search([
            ('event_category_id', '=', 13),
            ('date_begin', '>=', now),
        ])

        _logger.info(f"categ 13 events >> {events}")

        return request.render('website.ai-for-work-1_1b3066_13c129_7dfdcb', {
            'events': events,
        })

    @http.route('/introduction-to-cyber-security', type='http', auth="public", website=True)
    def get_upcoming_courses_14(self, **kw):
        # Switch to company 1 context
        company_1 = request.env['res.company'].sudo().browse(1)
        now = datetime.now()

        events = request.env['event.event'].sudo().with_company(company_1).search([
            ('event_category_id', '=', 14),
            ('date_begin', '>=', now),
        ])

        _logger.info(f"categ 1 events >> {events}")

        return request.render('website.ai-for-work-1_1b3066_1818e3', {
            'events': events,
        })

    @http.route('/bi-and-data-science', type='http', auth="public", website=True)
    def get_upcoming_courses_15(self, **kw):
        # Switch to company 1 context
        company_1 = request.env['res.company'].sudo().browse(1)
        now = datetime.now()

        events = request.env['event.event'].sudo().with_company(company_1).search([
            ('event_category_id', '=', 15),
            ('date_begin', '>=', now),
        ])

        _logger.info(f"categ 15 events >> {events}")

        return request.render('website.ai-for-work-1_3efddc_1086e0', {
            'events': events,
        })

    @http.route('/ai-for-social-media', type='http', auth="public", website=True)
    def get_upcoming_courses_16(self, **kw):
        # Switch to company 1 context
        company_1 = request.env['res.company'].sudo().browse(1)
        now = datetime.now()

        events = request.env['event.event'].sudo().with_company(company_1).search([
            ('event_category_id', '=', 16),
            ('date_begin', '>=', now),
        ])

        _logger.info(f"categ 16 events >> {events}")

        return request.render('website.ai-for-work-1_1b3066_13c129', {
            'events': events,
        })

