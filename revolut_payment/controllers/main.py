import logging
import pprint
import json
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class RevolutController(http.Controller):
    _return_url = "/payment/revolut/status"

    @http.route(_return_url, type='http', auth='public', methods=['GET', 'POST'], csrf=False, save_session=False)
    def revolut_return(self, **data):

        _logger.info("Received Revolut return data:\n%s", pprint.pformat(data))

        request.env['payment.transaction'].sudo()._handle_notification_data('revolut', data)
        return request.redirect('/payment/status')
