# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import content_disposition, Controller, request, route



class WebsiteRetailForm(http.Controller):

   @http.route(['/retail'], type='http', auth="public", website=True, sitemap=True)
   def appointment(self):
       partners = request.env['res.partner'].sudo().search([])
       values = {}
       values.update({
           'partners': partners
       })
       return request.render("4sight_crm.portal_retail_page", values)