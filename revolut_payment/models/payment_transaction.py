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
    revolut_transaction_id = fields.Char(string="revolut Transaction ID")


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

        return {'api_url': checkout_url}

    def _get_revolut_order_payload(self):

        base_url = self.provider_id.get_base_url()

        return {
            'amount': payment_utils.to_minor_currency_units(self.amount, self.currency_id),
            'currency': self.currency_id.name,
            "capture_mode": "manual",
            "customer": {
                'email': self.partner_id.email,
                'full_name': self.partner_id.name,
                'phone': self.partner_id.phone,
            },

            'redirect_url': urls.url_join("https://mdaoud.odoo.com", RevolutController._return_url)
        }

    def _get_vivawallet_transaction(self, data, match, key):
        return self.search([
            (match, '=', data.get(key)),
            ('provider_code', '=', 'revolut'),
            (match, '!=', False)
        ])

    def _get_tx_from_notification_data(self, provider, data):
        """ Override of payment to find the transaction based on revolut data.

        :param str provider: The provider of the acquirer that handled the transaction
        :param dict data: The notification data sent by the provider
        :return: The transaction if found
        :rtype: recordset of `payment.transaction`
        :raise: ValidationError if the data match no transaction
        """
        tx = super()._get_tx_from_notification_data(provider, data)
        if provider != 'revolut':
            return tx

        print('notification_data',data)

        tx = self._get_vivawallet_transaction(data, "vivawallet_order_code", "t")
        if not tx:
            tx = self._get_vivawallet_transaction(data, "vivawallet_order_code", "s")

        if not tx:
            raise ValidationError(
                "Vivawallet: " + _("No transaction found matching transaction reference %s.", data.get('t'))
            )

        return tx

    # def _process_notification_data(self, data):
    #     """ Override of payment to process the transaction based on Vivawallet data.
    #
    #     Note: self.ensure_one()
    #
    #     :param dict data: The notification data sent by the provider
    #     :return: None
    #     """
    #     super()._process_notification_data(data)
    #     if self.provider_code != 'vivawallet':
    #         return
    #
    #     if not data.get("t"):
    #         self._set_pending()
    #         return
    #
    #     self.vivawallet_transaction_id = data.get("t")
    #
    #     oauth_url, api_url, web_url = self.provider_id._vivawallet_endpoint()
    #     vivawallet_transaction = self.provider_id._vivawallet_make_request(
    #         endpoint=api_url,
    #         path="/checkout/v2/transactions/%s" % (self.vivawallet_transaction_id),
    #         method="GET"
    #     )
    #
    #     payment_status = VIVAWALLET_STATE_MAPPING[vivawallet_transaction.get("statusId")]
    #
    #     if payment_status == 'pending':
    #         self._set_pending()
    #     elif payment_status == 'authorized':
    #         self._set_authorized()
    #     elif payment_status == 'done':
    #         self._set_done()
    #     elif payment_status in ['cancel', 'error']:
    #         self._set_canceled("Vivawallet: " + _("Canceled payment with status: %s", payment_status))
    #     else:
    #         _logger.info("Received data with invalid payment status: %s", payment_status)
    #         self._set_error(
    #             "Vivawallet: " + _("Received data with invalid payment status: %s", payment_status)
    #         )
