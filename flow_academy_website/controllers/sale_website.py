from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


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
