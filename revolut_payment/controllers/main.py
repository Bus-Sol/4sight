import logging
import pprint
import json
from odoo import http
from odoo.http import request
from odoo.tools.misc import file_open

_logger = logging.getLogger(__name__)


class RevolutController(http.Controller):
    _return_url = "/payment/revolut/status"
    _apple_pay_domain_association_url = '/.well-known/apple-developer-merchantid-domain-association'


    @http.route(_return_url, type='http', auth='public', methods=['GET', 'POST'], csrf=False, save_session=False)
    def revolut_return(self, **data):

        _logger.info("Received Revolut return data:\n%s", pprint.pformat(data))

        request.env['payment.transaction'].sudo()._handle_notification_data('revolut', data)
        return request.redirect('/payment/status')

    @http.route(_apple_pay_domain_association_url, type='http', auth='public', csrf=False)
    def revolut_apple_pay_get_domain_association_file(self):
        """ Get the domain association file for Revolut's Apple Pay.

        :return: The content of the domain association file.
        :rtype: str
        """
        return file_open(
            'revolut_payment/static/files/apple-developer-merchantid-domain-association'
        ).read()
