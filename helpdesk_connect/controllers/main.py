# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request, route
import logging
_logger = logging.getLogger(__name__)
from werkzeug import urls
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo import SUPERUSER_ID
from urllib.parse import urlparse, parse_qs

class TrialPortal(http.Controller):

    @http.route('/portal/registrations', type='http', auth="public")
    def login_helpdesk(self, **kwargs):
        return request.render("helpdesk_connect.login_helpdesk")


    @http.route('/portal/check_user', type='json', auth="public",csrf=False)
    def check_for_users_email(self, email):
        login = email
        name = email.split('@')[0]
        values = request.params.copy()
        domain_mail = ''
        try:
            domain_mail = email.split('@')[1]
        except Exception as e:
            values['error'] = 'invalid Email!'
            return values
        exclued_domain = ('gmail', 'hotmail','yahoo')
        for word in exclued_domain:
            if word in domain_mail:
                values['error'] = 'Please use a business email address'
                return values
        _logger.info(
            "Attempt to send portal invite for <%s> by user <%s> from %s",
            login, request.env.user.login, request.httprequest.remote_addr)
        template = request.env.ref('helpdesk_connect.connect_to_portal')
        token = request.env['res.users'].generate_token_for_portal(name, login)
        if template:
            params = {
                'token': token,
                'user_id': name,
                'email': login
            }
            try:
                base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')

                Teams = request.env['helpdesk.team'].sudo().search([('website_published','=',True)], order='id desc')
                team_dict = {}
                for team in Teams:
                    #print(team, team.name)
                    team_dict['token_url_%s' %team.id] = [team.name , base_url + '/portal' + team.website_url + '?%s' % urls.url_encode(params)]
                # print(team_dict)
                with request._cr.savepoint():
                    template.sudo().with_context(user_mail=login,name=name, token_url=team_dict).send_mail(
                        SUPERUSER_ID, force_send=True, raise_exception=True)
                values['sent'] = True
            except Exception as e:
                values['error'] = e.args[0]
        return values


    @http.route('/portal/helpdesk/<string:team>', type='http',method='post', auth="public", website=True)
    def get_portal_user(self, request, team = None):
        url = request.httprequest.url
        parsed = urlparse(url)
        user_name = parse_qs(parsed.query)['user_id'][0]
        email = parse_qs(parsed.query)['email'][0]
        values = {'login':email,'name':user_name,'email':email,'password':user_name}
        token = request.env['res.users'].generate_token_for_portal(values['name'], values['login'])
        user_id = request.env['res.users'].sudo().search([('login','=',values['login'])])
        if token == parse_qs(parsed.query)['token'][0]:
            if user_id:
                if request.session.uid:
                    pass
                else:
                    request.params['password'] = values['password']
                    try:
                        uid = request.session.authenticate(request.session.db, values['login'], request.params['password'])
                        request.params['login_success'] = True
                        partner_id = self.assign_user_to_company(email.split('@')[1])
                        if partner_id:
                            user_id.partner_id.parent_id= partner_id
                    except Exception:
                        return http.redirect_with_hash('/')

            else:
                db, login, password = request.env['res.users'].sudo().signup(values, token=None)
                request.env.cr.commit()     # as authenticate will use its own cursor we need to commit the current transaction
                uid = request.session.authenticate(db, login, password)
                if not uid:
                    raise SignupError(_('Authentication Failed.'))
                else:
                    user_id = request.env['res.users'].sudo().search([('login','=',values['login'])])
                    partner_id = self.assign_user_to_company(email.split('@')[1])
                    if partner_id:
                        user_id.partner_id.parent_id= partner_id
            return http.redirect_with_hash('/helpdesk/%s' % team)
        else:
            return http.redirect_with_hash('/')

    def assign_user_to_company(self, domain_email):
        partner_email = {}
        partner_ids = request.env['res.partner'].sudo().search([])
        for partner in partner_ids:
            if partner.company_type == 'company':
                if partner.email: partner_email[partner.id] = partner.email
        for key, val in partner_email.items():
            if len(val.split('@')) > 1 and domain_email.lower() == val.split('@')[1].lower():
                return key
