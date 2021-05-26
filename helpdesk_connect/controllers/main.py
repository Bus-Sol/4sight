# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request, route
import logging
_logger = logging.getLogger(__name__)
from werkzeug import urls
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo import SUPERUSER_ID
import hashlib, uuid
import hmac


class TrialPortal(http.Controller):

    @http.route('/portal/registrations', type='http', auth="public")
    def login_helpdesk(self, **kwargs):
        return request.render("helpdesk_connect.login_helpdesk")


    @http.route('/portal/check_user', type='json', auth="public")
    def check_for_users_email(self, email):
        login = email
        name = email.split('@')[0]
        print(name)
        _logger.info(
            "Attempt to send portal invite for <%s> by user <%s> from %s",
            login, request.env.user.login, request.httprequest.remote_addr)
        template = request.env.ref('helpdesk_connect.connect_to_portal')
        token = request.env['res.users'].generate_token_for_portal(name, login)
        values = request.params.copy()
        if template:
            params = {
                'token': token,
                'user_id': name,
                'email': login
            }
            try:
                base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
                post_base_url = base_url + '/portal/helpdesk'
                token_url = post_base_url + '?%s' % urls.url_encode(params)
                with request._cr.savepoint():
                    template.sudo().with_context(user_mail=login,name=name, token_url=token_url).send_mail(
                        SUPERUSER_ID, force_send=True, raise_exception=True)
                values['sent'] = True
            except Exception as e:
                values['error'] = e.args[0]
        return values


    @http.route('/portal/helpdesk', type='http',method='post', auth="public", website=True)
    def get_portal_user(self, request):
        from urllib.parse import urlparse, parse_qs
        url = request.httprequest.url
        parsed = urlparse(url)
        print('request.session***',request.session)
        user_name = parse_qs(parsed.query)['user_id'][0]
        # salt = uuid.uuid4().hex
        # hashed_password = hmac.new(user_name.encode('utf-8'), salt.encode('utf-8'), hashlib.sha256).hexdigest()
        # print('*******hashed_password****',hashed_password)
        values = {'login':parse_qs(parsed.query)['email'][0],'name':parse_qs(parsed.query)['user_id'][0],'email':parse_qs(parsed.query)['email'][0],'password':parse_qs(parsed.query)['user_id'][0]}
        token = request.env['res.users'].generate_token_for_portal(values['name'], values['login'])
        user_id = request.env['res.users'].sudo().search([('login','=',values['login'])])
        if token == parse_qs(parsed.query)['token'][0]:
            if user_id:

                request.params['password'] = values['password']
                try:
                    # print('********user_id.password************', user_id.password)
                    # request.env.cr.execute("""UPDATE res_users SET password='your_new_password' WHERE login = 'admin' """)
                    # user_id.sudo().change_password(user_id.password, values['password'])
                    uid = request.session.authenticate(request.session.db, values['login'], request.params['password'])
                    request.params['login_success'] = True
                except Exception:
                    return http.redirect_with_hash('/')


            else:
                db, login, password = request.env['res.users'].sudo().signup(values, token=None)
                request.env.cr.commit()     # as authenticate will use its own cursor we need to commit the current transaction
                uid = request.session.authenticate(db, login, password)
                if not uid:
                    raise SignupError(_('Authentication Failed.'))

            return http.redirect_with_hash('/helpdesk')
        else:
            return http.redirect_with_hash('/')

