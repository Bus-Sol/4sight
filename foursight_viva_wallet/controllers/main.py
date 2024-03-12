# -*- coding: utf-8 -*-

import logging

import pprint
from odoo import _, http
from odoo.http import request
import requests

_logger = logging.getLogger(__name__)


class VivaController(http.Controller):
    _return_url = '/viva/return'
    _cancel_url = '/viva/cancel'

    @http.route(
        [_return_url, _cancel_url], type='http', auth='public', methods=['GET', 'POST'], csrf=False,
        save_session=False
    )
    def viva_return_from_redirect(self, **data):

        _logger.info("Viva Wallet: received data:\n%s", pprint.pformat(data))
        self.check_transaction(data)
        request.env['payment.transaction'].sudo()._handle_feedback_data('viva', data)
        return request.redirect('/payment/status')

    def check_transaction(self, data):
        order_code = data.get('s', False)
        transaction_id = data.get('t', False)
        tx = False
        if order_code:
            tx = request.env['payment.transaction'].sudo().search([('order_code', '=', order_code)])
        if transaction_id:
            access_token = tx.request_token()
            headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
            headers['Authorization'] = "Bearer %s" % access_token
            viva_url = 'https://api.vivapayments.com/checkout/v2/transactions/' if tx.acquirer_id.state == 'enabled' else 'https://demo-api.vivapayments.com/checkout/v2/transactions/'
            _logger.info('viva_url: %s' % viva_url)
            try:
                urequest = requests.get(url=viva_url + transaction_id, headers=headers)
                urequest.raise_for_status()
            except Exception:
                _logger.info("Viva Wallet: Could not find transaction ID")
                return data

            resp = urequest.json()
            if resp:
                data.update(resp)
        return data
