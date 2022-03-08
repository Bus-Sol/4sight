# -*- coding: utf-8 -*-
import json
from odoo import http
from odoo.http import content_disposition, Controller, request, route
import requests

class WebsiteRetailForm(http.Controller):

    @http.route(['/retail'], type='http', auth="public", website=True, sitemap=True)
    def post_customer_date(self, **kwargs):

        print('*****************************',kwargs, request.session)
        districts = request.env['cyprus.district'].sudo().search([])
        values = {
            'districts': districts,
        }
        return request.render("4sight_crm.portal_retail_page", values)

    @http.route(['/data/district/update_area_selection'], type='http', auth="public", methods=['POST'], website=True)
    def area_selection_json(self, district_id=None, **kwargs):

        print(district_id)
        list_items = []
        if district_id:
            district_key = request.env['cyprus.district'].sudo().search([('id','=',district_id)]).key
            list_items = request.env['cyprus.area'].sudo().search_read([('district_name','=',district_key)],['id', 'key', 'name'])
        print(list_items)
        return json.dumps(list_items)

    @http.route(['/data/district/update_street_api'], type='http', auth="public", methods=['POST'], website=True)
    def street_selection_json(self, district_key =None, name_inserted=None,area_key=None, **kwargs):

        print(name_inserted, district_key,area_key)
        user_lang = request.session['context']['lang']
        lng = 'el' if user_lang == 'el_GR' else 'en'
        list_items = []
        url = ''
        next_page = ''
        payload = {}
        headers = {
            'Authorization': 'eyJpdiI6IkdwUXJqZkQrOGNRK080TThiYUdOXC9RPT0iLCJ2YWx1ZSI6Ind1WHQzUmdOSDZ4cXdmbHlcL2pydCtYTFJJc1hpa0NQT0hOQVwvaExQaWE0RCt4b3ZOV2NZR09qZkdzR0tCVGJ1ZCIsIm1hYyI6IjBlNTExYjk0NGM2ZmVlOTAwNjk5ZTJjMzRkZTYyMWEyNjQ0ZTAyNGI5YWEzMmE4MGM2ZjgwZTczYTFkMmY2NjgifQ=='
        }

        if name_inserted and district_key:
            district_name = request.env['cyprus.district'].sudo().search([('id','=',district_key)],limit=1).key
            area = request.env['cyprus.area'].sudo().search([('id', '=', area_key)], limit=1).key
            if district_name in ['occupied-areas','government-authorities','post-office-boxes','parcel24']:
                url = "https://cypruspost.post/api/postal-codes/"+district_name+"?district="+area+"&param="+name_inserted+"&lng=en&page_token=" + next_page
            else:
                url = "https://cypruspost.post/api/postal-codes/search?district=" + district_name + "&area=" + area + "&param=" + name_inserted + "&lng="+lng+"&page_token=" + next_page

            while next_page != None:
                try:
                    url = url
                    response = requests.request("GET", url, headers=headers, data=payload)
                    res = response.json()
                    print(res)
                    if res['status_code'] == 400:
                        return json.dumps(['error'])
                    result = res['data']['result']
                    next_page = result['paginator']['tokens']['next_page']
                    list_items = list_items + res['data']['result']['items']
                except Exception as e:
                    print('*********', e)
                    break
        print(list_items)
        return json.dumps(list_items)