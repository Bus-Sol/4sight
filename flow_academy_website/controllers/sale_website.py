from odoo import fields, http, SUPERUSER_ID, tools, _
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
from werkzeug.exceptions import Forbidden

import logging
_logger = logging.getLogger(__name__)


class WebsiteEventSale(WebsiteSale):

    def _get_mandatory_fields_shipping(self, country_id=False):
        return ['email']

    def _get_mandatory_fields_billing(self, country_id=False):
        return ['email']

    def values_preprocess(self, values):
        new_values = super().values_preprocess(values)
        if new_values.get('company_type') == 'person':
            name = ''
            if new_values.get('firstname'):
                name += new_values.get('firstname')
            if new_values.get('lastname'):
                name += ' ' + new_values.get('lastname')
            new_values.update({
                'name': name,
            })
        return new_values

    @http.route(['/shop/checkout'], type='http', auth="public", website=True, sitemap=False)
    def checkout(self, **post):
        # 1. Retrieve the data from the session
        # We use .pop() so the data is deleted after being read (cleaner)
        custom_kwargs = request.session.get('custom_checkout_data', {})

        if custom_kwargs:
            # Now you can use your passed values

            event_id = custom_kwargs.get('event_id')
            categ_id = custom_kwargs.get('event_categ_id')
            post['event_id'] = event_id
            post['event_categ_id'] = categ_id
            if custom_kwargs.get('my_custom_flag'):
                _logger.info(f"Processing checkout for event: {custom_kwargs.get('event_name')}")

        # 2. Continue with the standard Odoo checkout logic
        return super(WebsiteEventSale, self).checkout(**post)

    @http.route('/shop/clear_and_back', type='http', auth="public", website=True)
    def clear_cart_and_back(self):
        # Get the current sale order (the cart)
        order = request.website.sale_get_order()
        if order:
            _logger.info(f"order to unlink >> {order}")
            # Option A: Completely delete the draft order
            order.unlink()
            # Option B: Just remove lines if you want to keep the order record
            # order.order_line.unlink()
        custom_kwargs = request.session.get('custom_checkout_data', {})
        _logger.info(f"custom_kwargs >> {custom_kwargs}")

        if custom_kwargs:
            # Now you can use your passed values
            categ_id = custom_kwargs.get('event_categ_id')
            if categ_id:
                _logger.info(f"event categ >> {categ_id}")

                return request.redirect(f'/events/type/{categ_id}')
            else:
                return request.redirect(f'/shop/cart')
        else:
            return request.redirect(f'/shop/cart')
        return True

    def _get_country_related_render_values(self, kw, render_values):
        """ Provide the fields related to the country to render the website sale form """
        values = render_values['checkout']
        _logger.info("Get render Values in country function...")
        custom_kwargs = request.session.get('custom_checkout_data', {})

        if custom_kwargs:
            # Now you can use your passed values

            event_id = custom_kwargs.get('event_id')
            categ_id = custom_kwargs.get('event_categ_id')
            _logger.info(f"event categ >> {categ_id}")
        _logger.info('render_values ?? %s', render_values)
        mode = render_values['mode']
        order = render_values['website_sale_order']

        def_country_id = order.partner_id.country_id
        if order._is_public_order():
            if request.geoip.country_code:
                def_country_id = request.env['res.country'].search([('code', '=', request.geoip.country_code)], limit=1)
            else:
                def_country_id = request.website.user_id.sudo().country_id

        country = 'country_id' in values and values['country_id'] != '' and request.env['res.country'].browse(
            int(values['country_id']))
        country = country and country.exists() or def_country_id

        res = {
            'country': country,
            'country_states': country.get_website_sale_states(mode=mode[1]),
            'countries': country.get_website_sale_countries(mode=mode[1]),
        }
        return res

    def values_postprocess(self, order, mode, values, errors, error_msg):
        new_values = {}
        authorized_fields = request.env['ir.model']._get('res.partner')._get_form_writable_fields()
        for k, v in values.items():
            # don't drop empty value, it could be a field to reset
            if k in authorized_fields and v is not None:
                new_values[k] = v
            else:  # DEBUG ONLY
                if k not in ('field_required', 'partner_id', 'callback', 'submitted'):  # classic case
                    _logger.debug("website_sale postprocess: %s value has been dropped (empty or not writable)" % k)

        if request.website.specific_user_account:
            new_values['website_id'] = request.website.id

        update_mode, address_mode = mode
        if update_mode == 'new':
            commercial_partner = order.partner_id.commercial_partner_id
            lang = request.lang.code if request.lang.code in request.website.mapped('language_ids.code') else None
            if lang:
                new_values['lang'] = lang
            new_values['company_id'] = request.website.company_id.id
            new_values['team_id'] = request.website.salesteam_id and request.website.salesteam_id.id
            new_values['user_id'] = request.website.salesperson_id.id

            if address_mode == 'billing':
                is_public_order = order._is_public_order()
                if is_public_order:
                    # New billing address of public customer will be their contact address.
                    new_values['type'] = 'contact'
                elif values.get('use_same'):
                    new_values['type'] = 'other'
                else:
                    new_values['type'] = 'invoice'

                # for public user avoid linking to default archived 'Public user' partner
                if commercial_partner.active:
                    new_values['parent_id'] = commercial_partner.id
            elif address_mode == 'shipping':
                new_values['type'] = 'delivery'
                new_values['parent_id'] = commercial_partner.id
        _logger.info(f"new_values data : {new_values}")
        return new_values, errors, error_msg

    def _checkout_form_save(self, mode, checkout, all_values):
        _logger.info(f"Saving checkout data : {checkout}")
        _logger.info(f"Saving checkout All data : {all_values}")

        if all_values.get('company_type') in ['person', 'company']:
            checkout['company_type'] = all_values.get('company_type')
            _logger.info(f"Saving new checkout val: {checkout['company_type']}")

        if all_values.get('firstname'):
            checkout['firstname'] = all_values.get('firstname')

        if all_values.get('lastname'):
            checkout['lastname'] = all_values.get('lastname')

        if all_values.get('privacy_terms'):
            checkout['privacy_terms'] = all_values.get('privacy_terms')

        if all_values.get('marketing_subscription'):
            checkout['marketing_subscription'] = all_values.get('marketing_subscription')

        Partner = request.env['res.partner']
        if mode[0] == 'new':
            partner_id = Partner.sudo().with_context(tracking_disable=True).create(checkout).id
        elif mode[0] == 'edit':
            partner_id = int(all_values.get('partner_id', 0))
            if partner_id:
                # double check
                order = request.website.sale_get_order()
                shippings = Partner.sudo().search([("id", "child_of", order.partner_id.commercial_partner_id.ids)])
                if partner_id not in shippings.mapped('id') and partner_id != order.partner_id.id:
                    return Forbidden()
                Partner.browse(partner_id).sudo().write(checkout)
        return partner_id
