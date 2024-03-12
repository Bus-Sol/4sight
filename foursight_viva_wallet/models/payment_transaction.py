# coding: utf-8

import json
import logging
import base64
from werkzeug import urls
from odoo.exceptions import ValidationError
from odoo import _, api, fields, models
from odoo.addons.foursight_viva_wallet.controllers.main import VivaController
import requests
from odoo.http import request

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    order_code = fields.Char('Order Code')

    def request_token(self):

        base64string = base64.encodebytes(
            bytes('%s:%s' % (self.acquirer_id.viva_client_public, self.acquirer_id.viva_client_secret), 'ascii'))
        decode_credentials = base64string.decode('ascii').replace('\n', '')
        headers = {'Content-Type': 'application/x-www-form-urlencoded',
                   "Authorization": "Basic %s" % decode_credentials
                   }
        grant_type = {'grant_type': 'client_credentials'}
        url_token = 'https://accounts.vivapayments.com/connect/token' if self.state == 'enabled' else \
            'https://demo-accounts.vivapayments.com/connect/token'
        response = requests.post(
            url=url_token,
            headers=headers, data=grant_type, timeout=300)
        _logger.info('Response token: %s', response.json())
        rslt = response.json()
        if response.status_code == 200:
            return rslt['access_token']
        else:
            if 'error' in rslt:
                raise ValidationError(_(rslt['error']))

    def create_order(self, token):

        url_create_order = 'https://api.vivapayments.com/checkout/v2/orders' if self.state == 'enabled' else 'https://demo-api.vivapayments.com/checkout/v2/orders'
        headers = {'Content-type': 'application/json'}
        headers['Authorization'] = "Bearer %s" % token
        payload = {
            'amount': self.amount * 100,
            'customerTrns': self.reference,
            'customer': {
                'email': self.partner_email,
                'fullName': self.partner_name,
                'phone': self.partner_phone,
                'countryCode': self.partner_country_id.code or '',
                'requestLang': self.partner_lang,
            }
        }
        req = requests.post(
            url=url_create_order,
            headers=headers, data=json.dumps(payload))
        if req.status_code == 200:
            res = req.json()
            if 'orderCode' in res:
                return res['orderCode']
            else:
                status = res['status']
                msg = res['message']
                error_msg = _(
                    "Something went wrong during your order generation. Status = %s, Message Error: %s",
                    status, msg)
                raise ValidationError(error_msg)
        else:
            raise ValidationError(req.reason)

    def _get_specific_rendering_values(self, processing_values):

        res = super()._get_specific_rendering_values(processing_values)
        if self.code != 'viva':
            return res

        base_url = self.acquirer_id.get_base_url()
        success_url = urls.url_join(base_url, VivaController._return_url)
        declined_url = urls.url_join(base_url, VivaController._cancel_url)
        token = self.request_token()
        _logger.info('Token: %s', token)
        if token:
            txn = self.env['payment.transaction'].search([('reference', '=', self.reference)])
            order_code = self.create_order(token)
            request.session['order_code'] = order_code
        else:
            return False
        _logger.info('Checking if session containes OrderCode: %s', request.session)

        api_url = 'https://www.vivapayments.com/web/newtransaction.aspx?ref=' \
            if self.acquirer_id.state == 'enabled' \
            else 'https://demo.vivapayments.com/web/newtransaction.aspx?ref='

        viva_tx_values = {
            'Viva_return': success_url,
            'Viva_returncancel': declined_url,
            'api_url': api_url + str(order_code),
        }
        if txn:
            txn.order_code = order_code
        return viva_tx_values

    @api.model
    def _get_tx_from_feedback_data(self, code, data):

        tx = super()._get_tx_from_feedback_data(code, data)
        if code != 'viva':
            return tx

        reference = data.get('s')
        tx = self.search([('order_code', '=', reference), ('code', '=', 'viva')])
        if not tx:
            raise ValidationError(
                "VivaWallet: " + _("No transaction found matching Order Ref %s.", reference)
            )
        return tx

    def _process_notification_data(self, data):

        super()._process_notification_data(data)
        if self.code != 'viva':
            return

        _logger.info('Entering validation with Viva Wallet payment: %s' % data)
        status = data.get('statusId', False)
        if data.get('t'):
            if status == 'F':
                self.write({'acquirer_reference': data.get('t')})
                _logger.info('Validated for Viva Wallet payment %s: set as done' % (self.reference))
                self._set_done()
                return True

            elif status in ['A', 'C']:
                self.update(state_message=data.get('Active/Captured', ''))
                self._set_pending()
                self.write({'acquirer_reference': data.get('t')})
                _logger.info('Received notification for Viva Wallet payment %s: set as pending' % (self.reference))
            else:
                error = 'Received unrecognized status for Viva Wallet payment %s: %s, set as error' % (
                    self.reference, status)
                self.update(state_message=error)
                self._set_canceled()
                _logger.info(error)
                self.write({'acquirer_reference': data.get('t')})
        else:
            _logger.info('Data: %s', data)
            if 'Success' in data and data['Success'] == True:
                self.write({'acquirer_reference': data.get('TransactionId')})
                self._set_done()
            elif 'ErrorText' in data:
                self.write({'state_message': data['ErrorText']})
                self._set_error()
            elif 'Message' in data:
                self.write({'state_message': 'Unknown reason, please check your logfile'})
                self._set_canceled()
            else:
                self.write({'state_message': 'Unknown reason, please check your logfile'})
                self._set_canceled()
