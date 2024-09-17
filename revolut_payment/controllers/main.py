import logging
import pprint
import json
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class RevolutController(http.Controller):
    _return_url = "/payment/revolut/status"
    _webhook_url = "/payment/revolut/webhook"

    @http.route(_return_url, type='http', auth='public', methods=['GET', 'POST'], csrf=False, save_session=False)
    def revolut_return(self, **data):
        """ Process the data returned by Vivawallet after redirection.

        The route is flagged with `save_session=False` to prevent Odoo from assigning a new session
        to the user if they are redirected to this route with a POST request. Indeed, as the session
        cookie is created without a `SameSite` attribute, some browsers that don't implement the
        recommended default `SameSite=Lax` behavior will not include the cookie in the redirection
        request from the payment provider to Odoo. As the redirection to the '/payment/status' page
        will satisfy any specification of the `SameSite` attribute, the session of the user will be
        retrieved and with it the transaction which will be immediately post-processed.

        :param dict data: The notification data (only order code `s`) if order is pending or
                        the transaction reference (`t`) if transaction is created.
        """
        _logger.info("Received Revolut return data:\n%s", pprint.pformat(data))

        request.env['payment.transaction'].sudo()._handle_notification_data('revolut', data)
        return request.redirect('/payment/status')


    @http.route(_webhook_url, type='json', auth='public', methods=['POST'], csrf=False)
    def revolut_webhook(self, **data):
        """ Process the data returned by Revolut after webhook is called.

        Odoo will not update payment.transaction state directly via webhook since can't be trusted.
        Instead _handle_notification_data will be called again
        """
        _logger.info("Received Revolut webhook data:\n%s", pprint.pformat(data))

        if data.get("EventData"):
            print('webhook data', data.get("EventData"))
            data['t'] = data['EventData']['TransactionId']
            data['s'] = data['EventData']['OrderCode']

            _logger.info("Handling Revolut webhook transaction: %s" % (data['t']))
            request.env['payment.transaction'].sudo()._handle_notification_data('revolut', data)

        return http.Response(status=200)