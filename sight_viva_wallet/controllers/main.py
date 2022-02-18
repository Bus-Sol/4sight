# -*- coding: utf-8 -*-
import logging
import pprint
import werkzeug
import requests
from odoo import http
from odoo.http import request
from odoo.addons.payment.models.payment_acquirer import ValidationError

_logger = logging.getLogger(__name__)


class VivaController(http.Controller):
    _return_url = '/viva/return'
    _cancel_url = '/payment/viva/cancel'

    @http.route(_return_url, type='http', csrf=False, auth='public')
    def viva_return(self, **post):
        try:
            res = self.viva_validate_data(**post)
        except ValidationError:
            _logger.exception('Validating the Viva Wallet payment')
        return werkzeug.utils.redirect('/payment/process')

    @http.route(_cancel_url, type='http', auth="public", csrf=False)
    def viva_cancel(self, **post):
        """ When the user cancels its Paypal payment: GET on this route """
        try:
            res = self.viva_validate_data(**post)
        except ValidationError:
            _logger.exception('Unable to validate the Viva Wallet payment')
        return werkzeug.utils.redirect('/payment/process')

    def get_transaction_url(self, tx):
        environment = 'prod' if tx.state == 'enabled' else 'test'
        return tx.acquirer_id._get_viva_urls(environment)['viva_rest_trx']

    def viva_validate_data(self, **post):
        _logger.info('Entering controller: %s' % post)
        res = False
        reference = post.get('s')
        tx = None
        viva_transaction_id = post.get('t', False)
        _logger.info('viva_transaction_id: %s' % viva_transaction_id)
        if reference:
            tx = request.env['payment.transaction'].sudo().search([('order_code', '=', reference)])
        if not tx:
            _logger.warning('Received notification for unknown payment reference')
            return False
        if not viva_transaction_id:
            _logger.warning('Received notification for unknown payment transaction reference')
            return False
        _logger.info('TX: %s' % tx)
        access_token = tx.acquirer_id.request_token()
        headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
        headers['Authorization'] = "Bearer %s" % access_token
        viva_url = 'https://api.vivapayments.com/checkout/v2/transactions/' + viva_transaction_id
        _logger.info('viva_url: %s' % viva_url)
        urequest = requests.get(url=viva_url, headers=headers)
        urequest.raise_for_status()
        resp = urequest.json()
        _logger.info('resp: %s' % resp)
        if resp['statusId']:
            if resp['statusId'] == 'F':
                _logger.info('Viva Wallet: validated data')
                post['cardNumber'] = resp['cardNumber']
                post['statusId'] = resp['statusId']
                res = request.env['payment.transaction'].sudo().form_feedback(post, 'viva')
            elif resp['statusId'] in ['A','C']:
                _logger.info('Viva Wallet: Captured/Activated data')
                post['cardNumber'] = resp['cardNumber']
                post['statusId'] = resp['statusId']
                res = request.env['payment.transaction'].sudo().form_feedback(post, 'viva')
            elif resp['statusId'] == 'E':
                _logger.warning('Viva Wallet: answered INVALID/FAIL on data verification')
                if tx:
                    tx._set_transaction_error('Invalid response from Viva Wallet. Please contact your administrator.')
            else:
                _logger.warning(
                    'Viva Wallet: unrecognized Viva Wallet answer, received ERROR instead of VERIFIED/SUCCESS or INVALID/FAIL')
                if tx:
                    tx._set_transaction_error('Unrecognized error from Viva Wallet. Please contact your administrator.')
        return res
