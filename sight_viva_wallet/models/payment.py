# coding: utf-8
import json
import logging
import requests
import pprint
from werkzeug import urls
import base64
from odoo import api, fields, models, _
from odoo.http import request
from odoo.addons.sight_viva_wallet.controllers.main import VivaController
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PaymentAcquirerViva(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[
        ('viva', 'Viva')
    ], ondelete={'viva': 'set default'})
    viva_secret_key = fields.Char(required_if_provider='viva', groups='base.group_user')
    viva_publishable_key = fields.Char(required_if_provider='viva', groups='base.group_user')
    viva_image_url = fields.Char(
        "Checkout Image URL", groups='base.group_user',
        help="A relative or absolute URL pointing to a square image of your "
             "brand or product. As defined in your Viva Wallet profile. See: "
             "https://viva.com/docs/checkout")
    viva_client_id = fields.Char(required_if_provider='viva', groups='base.group_user')
    viva_client_secret = fields.Char(required_if_provider='viva', groups='base.group_user')

    @api.model
    def _get_viva_urls(self, environment):
        """ Viva URLS """
        if environment == 'prod':
            return {
                'viva_form_url': 'https://www.vivapayments.com/web/newtransaction.aspx?ref=',
                'viva_rest_token': 'https://accounts.vivapayments.com/connect/token',
                'viva_rest_url': 'https://api.vivapayments.com/checkout/v2/orders',
                'viva_rest_trx': 'https://api.vivapayments.com/checkout/v2/transactions/',
            }
        else:
            return {
                'viva_form_url': 'https://demo.vivapayments.com/web/newtransaction.aspx?ref=',
                'viva_rest_token': 'https://demo-accounts.vivapayments.com/connect/token',
                'viva_rest_url': 'https://demo-api.vivapayments.com/checkout/v2/orders',
                'viva_rest_trx': 'https://demo-api.vivapayments.com/checkout/v2/transactions/',
            }

    def request_token(self):

        base64string = base64.encodebytes(bytes('%s:%s' % (self.viva_client_id, self.viva_client_secret), 'ascii'))
        decode_credentials = base64string.decode('ascii').replace('\n', '')
        headers = {'Content-Type': 'application/x-www-form-urlencoded',
                   "Authorization": "Basic %s" % decode_credentials
                   }
        grant_type = {'grant_type': 'client_credentials'}
        environment = 'prod' if self.state == 'enabled' else 'test'
        url_token = self._get_viva_urls(environment)['viva_rest_token']
        response = requests.post(
            url=url_token,
            headers=headers, data=grant_type, timeout=60)
        _logger.info('Response token: %s', response.json())
        rslt = response.json()
        if response.status_code == 200:
            return rslt['access_token']
        else:
            if 'error' in rslt:
                raise ValidationError(_(rslt['error']))

    def create_order(self, token, viva_tx_values):

        environment = 'prod' if self.state == 'enabled' else 'test'
        url_create_order = self._get_viva_urls(environment)['viva_rest_url']
        headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
        headers['Authorization'] = "Bearer %s" % token
        payload = json.dumps({
            'amount': viva_tx_values['amount'] * 100,
            'customerTrns': viva_tx_values['reference'],
            'customer': {
                'email': viva_tx_values['partner_email'],
                'fullName': viva_tx_values['partner_name'],
                'phone': viva_tx_values['partner_phone'],
                'countryCode': viva_tx_values.get('partner_country') and viva_tx_values.get(
                    'partner_country').code or '',
                'requestLang': viva_tx_values['partner_lang'],
            }
        })
        req = requests.post(
            url=url_create_order,
            headers=headers, data=payload, timeout=60)
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

    def viva_form_generate_values(self, values):
        self.ensure_one()
        token = self.request_token()
        _logger.info('Token: %s', token)
        order_code = False
        if token:
            order_code = self.create_order(token, values)
            request.session['order_code'] = order_code
        else:
            return False
        _logger.info('Checking if session containes OrderCode: %s', request.session)
        base_url = self.get_base_url()
        viva_tx_values = dict(values)
        viva_tx_values.update({
            'Viva_return': urls.url_join(base_url, VivaController._return_url),
            'Viva_returncancel': urls.url_join(base_url, VivaController._cancel_url),
        })
        txn = self.env['payment.transaction'].search([('reference', '=', viva_tx_values['reference'])])
        if txn:
            txn.order_code = order_code
        return viva_tx_values

    def viva_get_form_action_url(self):
        self.ensure_one()
        environment = 'prod' if self.state == 'enabled' else 'test'
        return self._get_viva_urls(environment)['viva_form_url'] + str(request.session['order_code'])


class PaymentTransactionViva(models.Model):
    _inherit = 'payment.transaction'

    order_code = fields.Char('Order Code')

    @api.model
    def _viva_form_get_tx_from_data(self, data):
        reference, txn_id = data.get('s'), data.get('t')
        if not reference or not txn_id:
            error_msg = _('Viva Wallet: received data with missing reference (%s) or txn-id (%s))') % (
                reference, txn_id)
            _logger.error(error_msg)
            raise ValidationError(error_msg)
        tx = self.search([('order_code', '=', reference)])
        if not tx or len(tx) > 1:
            error_msg = _('Viva Wallet: received data for reference %s') % (reference)
            if not tx:
                error_msg += _('; no order found')
            else:
                error_msg += _('; multiple order found')
            _logger.info(error_msg)
            raise ValidationError(error_msg)
        return tx

    def _viva_form_get_invalid_parameters(self, data):
        invalid_parameters = []
        # reference at acquirer: pspReference
        if self.acquirer_reference and data.get('t') != self.acquirer_reference:
            invalid_parameters.append(('Tx Ref', data.get('t'), self.acquirer_reference))
        # seller
        # result
        if not data.get('statusId'):
            invalid_parameters.append(('statusId', data.get('statusId'), 'something'))

        return invalid_parameters

    def _viva_form_validate(self, data):
        _logger.info('Entering validation with Viva Wallet payment: %s' % data)
        status = data.get('statusId', False)
        if data.get('t'):
            last4 = data.get('cardNumber', '')[-4:]
            payment_token = self.env['payment.token'].sudo().create({
                'acquirer_id': self.acquirer_id.id,
                'partner_id': self.partner_id.id,
                'name': 'XXXXXXXXXXXX%s' % last4,
                'acquirer_ref': data.get('t')
            })
            if status == 'F':
                self._set_transaction_done()
                self.write({'acquirer_reference': data.get('t'),
                            'payment_token_id': payment_token.id})
                _logger.info('Validated for Viva Wallet payment %s: set as done' % (self.reference))
                return True

            elif status in ['A', 'C']:
                self.update(state_message=data.get('Active/Captured', ''))
                self._set_transaction_pending()
                self.write({'acquirer_reference': data.get('t'),
                            'payment_token_id': payment_token.id})
                _logger.info('Received notification for Viva Wallet payment %s: set as pending' % (self.reference))
                return True
            else:
                error = 'Received unrecognized status for Viva Wallet payment %s: %s, set as error' % (
                    self.reference, status)
                self.update(state_message=error)
                self._set_transaction_cancel()
                _logger.info(error)
                self.write({'acquirer_reference': data.get('t'),
                            'payment_token_id': data.get('cardNumber')})
                return True
