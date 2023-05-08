# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.translate import _
import requests
import json

PAYROLL_CODE = ['7002', '7003', '7004', '7005', '2210']


class AccountMove(models.Model):
    _inherit = "account.move"

    is_payroll = fields.Boolean('Payroll Journal')

    def action_load_payroll_accounts(self):
        accounts = self.env['account.account'].search([('code', 'in', PAYROLL_CODE)])
        if not self.line_ids:

            account_move_lines = [(0, 0, {'account_id': account.id, 'name': account.name}) for account in accounts]
            self.write({'line_ids': account_move_lines})
        pass


    def make_connexion(self):
        url = "https://developers-gateway.shireburn.com/v1/OAuth/requesttoken"

        payload={}
        headers = {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        }

        response = requests.request("GET", url, headers=headers, data=payload)

        print(response.text)

        url = "https://developers-gateway.shireburn.com/v1/OAuth/requesttoken"

        payload={}
        headers = {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        }

        response = requests.request("GET", url, headers=headers, data=payload)

        print(response.text)

        ## Access Token

        url = "https://developers-gateway.shireburn.com/v1/OAuth/accesstoken?requestToken=b53e810d88494f1fba4f3ed6a2ee21c0&username=ad_wells@hotmail.com&password=Odoo-ind01!&persistent=true"

        payload={}
        headers = {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        }

        response = requests.request("GET", url, headers=headers, data=payload)

        print(response.text)

        ## Open APi key

        url = "https://developers-gateway.shireburn.com/v1/OAuth/openapikey"

        payload = json.dumps({
          "OpenApiKeyType": 1,
          "OpenApiKeyDescription": "My Test Open Api Key"
        })
        headers = {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'Authorization': 'OAuth 6348c162d0bc4c1f92cd25d6ec80a807' # accessToken
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        print(response.text)

        # Get employees
        url = "https://developers-gateway.shireburn.com/payroll/v1/payrolls?CompanyCode=00001"

        payload={}
        headers = {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          'subscription-key': '128576387bf14fc9b2ce5aedef9e583a',
          'Authorization': 'OAuth aa40175350454925930d1be65600f209'
        }

        response = requests.request("GET", url, headers=headers, data=payload)

        print(response.text)