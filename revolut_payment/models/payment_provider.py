from werkzeug import urls
from requests.auth import HTTPBasicAuth
from odoo import _, api, fields, models, service
from odoo.exceptions import ValidationError
from odoo.addons.revolut_payment.const import SUPPORTED_CURRENCIES, DEFAULT_PAYMENT_METHODS_CODES
import logging
import requests
import json
import pprint


_logger = logging.getLogger(__name__)

class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('revolut', "Revolut")],
        ondelete={'revolut': 'set default'}
    )

    revolut_merchant_api_public = fields.Char(
        string="Merchant Public API Key",
        required_if_provider='revolut'
    )

    revolut_merchant_api_secret = fields.Char(
        string="Merchant Secret API Key",
        required_if_provider='revolut'
    )

    def _get_supported_currencies(self):
        """ Override of `payment` to return the supported currencies. """
        supported_currencies = super()._get_supported_currencies()
        if self.code == 'revolut':
            supported_currencies = supported_currencies.filtered(
                lambda c: c.name in SUPPORTED_CURRENCIES
            )
        return supported_currencies

    def _revolut_endpoint(self):
        """ Returns correct revolut endpoint based on acquirer environment
        """
        if self.state != "test":
            return "https://merchant.revolut.com/"
        else:
            return "https://sandbox-merchant.revolut.com/"


    def _revolut_make_request(self, endpoint, path, data=None, method='POST'):
        """ Make a request at revolut endpoint.

        Note: self.ensure_one()

        :param str endpoint: The endpoint to be reached by the request
        :param dict data: The payload of the request
        :param str method: The HTTP method of the request
        :return The JSON-formatted content of the response
        :rtype: dict
        :raise: ValidationError if an HTTP error occurs
        """
        self.ensure_one()

        url = urls.url_join(endpoint, path)
        # odoo_version = service.common.exp_version()['server_version']
        # module_version = self.env.ref('base.module_payment_vivawallet').installed_version
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Revolut-Api-Version": "2024-05-01",
            "Authorization": "Bearer %s" % self.revolut_merchant_api_secret
        }

        try:
            response = requests.request(method, url, json=data, headers=headers, timeout=60)
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError:
                _logger.exception(
                    "Invalid API request at %s with data:\n%s", url, pprint.pformat(data)
                )
                raise ValidationError(
                    "Revolut: " + _(
                        "The communication with the API failed. Revolut gave us the following "
                        "information: %s", response.json().get('message', '')
                    ))
        except requests.exceptions.RequestException:
            _logger.exception("Unable to communicate with Revolut: %s", url)
            raise ValidationError("revolut: " + _("Could not establish the connection to the API."))

        return response.json()

    def _get_default_payment_method_codes(self):
        """ Override of `payment` to return the default payment method codes. """
        default_codes = super()._get_default_payment_method_codes()
        if self.code != 'revolut':
            return default_codes
        return DEFAULT_PAYMENT_METHODS_CODES

    def _compute_feature_support_fields(self):
        """ Override of `payment` to enable additional features. """
        super()._compute_feature_support_fields()
        self.filtered(lambda p: p.code == 'revolut').update({
            'support_manual_capture': 'full_only',
            'support_refund': 'partial',
            'support_tokenization': True,
        })