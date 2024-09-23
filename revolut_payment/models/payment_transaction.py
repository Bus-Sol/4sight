import logging
import pprint

from werkzeug import urls
from werkzeug.datastructures import MultiDict

from odoo import _, models, fields
from odoo.exceptions import ValidationError
from odoo.addons.payment import utils as payment_utils
from odoo.addons.revolut_payment.controllers.main import RevolutController


_logger = logging.getLogger(__name__)

class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    revolut_order_code = fields.Char(string="Revolut Order Code")
    revolut_order_token = fields.Char(string="Revolut Order Token")


    def _get_specific_rendering_values(self, processing_values):
        """ Override of payment to return Vivawallet-specific rendering values.

        Note: self.ensure_one() from `_get_processing_values`

        :param dict processing_values: The generic and specific processing values of the transaction
        :return: The dict of acquirer-specific rendering values
        :rtype: dict
        """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'revolut':
            return res

        api_url = self.provider_id._revolut_endpoint()
        path = 'api/orders'
        # url = urls.url_join(api_url, 'api/orders')
        payload = self._get_revolut_order_payload()
        _logger.info("sending request for link creation:\n%s", pprint.pformat(payload))
        payment_data = self.provider_id._revolut_make_request(
            endpoint=api_url,
            path=path,
            data=payload
        )
        # print('payment_data', payment_data)

        # The acquirer reference is set now to allow fetching the payment status after redirection
        self.revolut_order_code = payment_data.get('id')
        self.revolut_order_token = payment_data.get('token')
        checkout_url = payment_data.get('checkout_url')
        parsed_url = urls.url_parse(checkout_url)
        url_params = urls.url_decode(parsed_url.query)
        return {'api_url': checkout_url, 'url_params': url_params}

    def _get_revolut_order_payload(self):

        base_url = self.provider_id.get_base_url()
        rediredt_url = urls.url_join(base_url, RevolutController._return_url)

        return {
            'amount': payment_utils.to_minor_currency_units(self.amount, self.currency_id),
            'currency': self.currency_id.name,
            "capture_mode": "automatic",
            "customer": {
                'email': self.partner_id.email,
                'full_name': self.partner_id.name,
                'phone': self.partner_id.phone,
            },

            'redirect_url': f'{rediredt_url}?ref={self.reference}'
        }

    def _get_tx_from_notification_data(self, provider, notification_data):
        """ Override of payment to find the transaction based on revolut data.

        :param str provider: The provider of the acquirer that handled the transaction
        :param dict data: The notification data sent by the provider
        :return: The transaction if found
        :rtype: recordset of `payment.transaction`
        :raise: ValidationError if the data match no transaction
        """
        tx = super()._get_tx_from_notification_data(provider, notification_data)
        if provider != 'revolut':
            return tx

        print('notification_data',notification_data)

        tx = self.search(
            [('reference', '=', notification_data.get('ref')), ('provider_code', '=', 'revolut')]
        )
        if not tx:
            raise ValidationError("Revolut: " + _(
                "No transaction found matching reference %s.", notification_data.get('ref')
            ))
        return tx

    def _process_notification_data(self, notification_data):
        """ Override of payment to process the transaction based on Revolut data.

        Note: self.ensure_one()

        :param dict notification_data: The notification data sent by the provider
        :return: None
        """
        super()._process_notification_data(notification_data)
        if self.provider_code != 'revolut':
            return

        api_url = self.provider_id._revolut_endpoint()
        path = f'api/orders/{self.revolut_order_code.strip()}'

        payment_data = self.provider_id._revolut_make_request(
            endpoint=api_url,
            path=path,
            data=None,
            method='GET'
        )

        # Update the payment state.
        payment_status = payment_data.get('state')
        if payment_status in ['pending','processing']:
            self._set_pending()
        elif payment_status == 'authorised':
            self._set_authorized()
        elif payment_status == 'completed':
            self._set_done()
        elif payment_status in ['cancelled', 'failed']:
            self._set_canceled("Revolut: " + _("Canceled payment with status: %s", payment_status))
        else:
            _logger.info(
                "received data with invalid payment status (%s) for transaction with reference %s",
                payment_status, self.reference
            )
            self._set_error(
                "Revolut: " + _("Received data with invalid payment status: %s", payment_status)
            )

