# coding: utf-8
import logging
from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)

class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('viva', "Viva Wallet")], ondelete={'viva': 'set default'})
    viva_client_public = fields.Char(required_if_provider='viva')
    viva_client_secret = fields.Char(required_if_provider='viva')

    @api.model
    def _get_compatible_acquirers(self, *args, is_validation=False, **kwargs):
        acquirers = super()._get_compatible_acquirers(*args, is_validation=is_validation, **kwargs)

        if is_validation:
            acquirers = acquirers.filtered(lambda a: a.code != 'viva')

        return acquirers

    def _viva_get_api_url(self, api_key):
        self.ensure_one()
        if self.state == 'enabled':
            api_urls = {
                'viva_form_url': 'https://www.vivapayments.com/web/newtransaction.aspx?ref=',
                'viva_rest_token': 'https://accounts.vivapayments.com/connect/token',
                'viva_rest_url': 'https://api.vivapayments.com/checkout/v2/orders',
            }
        else:
            api_urls = {
                'viva_form_url': 'https://demo.vivapayments.com/web/newtransaction.aspx?ref=',
                'viva_rest_token': 'https://demo-accounts.vivapayments.com/connect/token',
                'viva_rest_url': 'https://demo-api.vivapayments.com/checkout/v2/orders',
            }
        return api_urls

    def _get_default_payment_method_id(self):
        self.ensure_one()
        if self.code != 'viva':
            return super()._get_default_payment_method_id()
        return self.env.ref('foursight_viva_wallet.payment_method_viva').id