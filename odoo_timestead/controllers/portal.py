# -*- coding: utf-8 -*-
from odoo import http, fields
from odoo.exceptions import AccessError, MissingError, UserError
from odoo.http import request
from odoo.tools.translate import _
from collections import OrderedDict
from odoo.addons.portal.controllers.portal import pager as portal_pager, CustomerPortal
from odoo.addons.portal.controllers.mail import _message_post_helper
import binascii


class PortalJobsheet(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id
        Service = request.env['jobsheet.service']

        if 'jobsheet_count' in counters:
            values['jobsheet_count'] = (
                request.env['client.jobsheet'].search_count([])
                if request.env['client.jobsheet'].check_access_rights('read', raise_exception=False)
                else 0
            )

        if 'service_count' in counters:
            values['service_count'] = Service.search_count(self._prepare_service_domain(partner)) \
                if Service.check_access_rights('read', raise_exception=False) else 0
        return values


    def _prepare_service_domain(self, partner):
        return [
            ('partner_service_id', 'child_of', [partner.commercial_partner_id.id])
        ]


    def _prepare_service_portal_rendering_values(
        self, page=1,  sortby=None, **kwargs
    ):
        Service = request.env['jobsheet.service'].sudo()

        partner = request.env.user.partner_id
        values = self._prepare_portal_layout_values()


        url = "/my/services"
        domain = self._prepare_service_domain(partner)

        pager_values = portal_pager(
            url=url,
            total=Service.search_count(domain),
            page=page,
            step=self._items_per_page,
        )
        Services = Service.search(domain, limit=self._items_per_page, offset=pager_values['offset'])
        # print('services', Services)
        lines = []

        tks = False
        for service in Services:
            planned = 0
            effective = 0
            remaining = 0
            tks1 = request.env['project.task'].sudo().search(
                [('partner_id', '=', partner.id),
                 ('related_service_id', '=', service.product_id.id),
                 ('sale_line_id', '!=', False),
                 ('sale_line_id.order_id.state', 'in', ['sale', 'done'])],
                order='id desc')
            # print('tasks', tks1)

            tks = [task for task in tks1 if round(task.remaining_hours, 2) > 0]

            for tsk in tks:
                planned += tsk.allocated_hours
                effective += tsk.effective_hours
                remaining += tsk.remaining_hours

            lines.append({
                'service': service.product_id.name,
                'planned': planned,
                'effective': effective,
                'remaining': remaining,
            })

        # print('lines', lines)

        values.update({
            'services': Services,
            'lines': lines,
            'page_name': 'service',
            'pager': pager_values,
            'default_url': url,
            'sortby': sortby,
        })

        return values

    @http.route(['/my/services', '/my/services/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_quotes(self, **kwargs):
        values = self._prepare_service_portal_rendering_values(**kwargs)
        return request.render("odoo_timestead.portal_my_services", values)



    def _jobsheet_get_page_view_values(self, jobsheet, access_token, **kwargs):
        values = {
            'page_name': 'jobsheet',
            'jobsheet': jobsheet,
        }
        return self._get_page_view_values(jobsheet, access_token, values, 'my_jobsheets_history', False, **kwargs)

    @http.route(['/my/jobsheets', '/my/Jobsheets/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_jobsheets(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        JobSheets = request.env['client.jobsheet']

        domain = []

        searchbar_sortings = {
            'date': {'label': _('Date'), 'order': 'date_order desc'},
            'name': {'label': _('Reference'), 'order': 'name desc'},
            'state': {'label': _('Status'), 'order': 'status'},
        }
        # default sort by order
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
        }
        # default filter by value
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']


        # count for pager
        jobsheet_count = JobSheets.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/Jobsheets",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=jobsheet_count,
            page=page,
            step=self._items_per_page
        )
        # content according to pager and archive selected
        jobsheets = JobSheets.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_invoices_history'] = jobsheets.ids[:100]

        values.update({
            'date': date_begin,
            'jobsheets': jobsheets,
            'page_name': 'jobsheet',
            'pager': pager,
            'default_url': '/my/jobsheets',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
        })
        return request.render("odoo_timestead.portal_my_jobsheets", values)

    @http.route(['/my/jobsheets/<int:job_id>'], type='http', auth="public", website=True)
    def portal_my_jobsheet_detail(self, job_id, access_token=None, message=False, report_type=None, download=False, **kw):
        try:
            job_sudo = self._document_check_access('client.jobsheet', job_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=job_sudo, report_type=report_type, report_ref='odoo_timestead.client_jobsheets', download=download)

        if job_sudo:
            # store the date as a string in the session to allow serialization
            now = fields.Date.today().isoformat()
            session_obj_date = request.session.get('view_jobsheet_%s' % job_sudo.id)
            if session_obj_date != now and request.env.user.share and access_token:
                request.session['view_jobsheet_%s' % job_sudo.id] = now
                body = _('Jobsheet viewed by customer %s', job_sudo.partner_id.name)
                _message_post_helper(
                    "client.jobsheet",
                    job_sudo.id,
                    body,
                    token=job_sudo.access_token,
                    message_type="notification",
                    subtype_xmlid="mail.mt_note",
                    partner_ids=job_sudo.user_id.sudo().partner_id.ids,
                )
        values = self._jobsheet_get_page_view_values(job_sudo, access_token, **kw)
        values['message'] = message

        return request.render("odoo_timestead.portal_jobsheet_page", values)

    @http.route(['/my/jobsheets/<int:job_id>/accept'], type='json', auth="public", website=True)
    def portal_jobsheet_accept(self, job_id, access_token=None, name=None, signature=None):
        # get from query string if not on json param
        access_token = access_token or request.httprequest.args.get('access_token')
        try:
            job_sudo = self._document_check_access('client.jobsheet', job_id, access_token=access_token)
        except (AccessError, MissingError):
            return {'error': _('Invalid order.')}

        if not signature:
            return {'error': _('Signature is missing.')}

        try:
            job_sudo.write({
                'signee': name,
                # 'signed_on': fields.Datetime.now(),
                'signature': signature,
                'status': 'signed'
            })
            request.env.cr.commit()
        except (TypeError, binascii.Error) as e:
            return {'error': _('Invalid signature data.')}


        pdf = request.env.ref('odoo_timestead.client_jobsheets').sudo()._render_qweb_pdf([job_sudo.id])[0]

        _message_post_helper(
            'client.jobsheet', job_sudo.id, _('Jobsheet signed by %s on %s') % (name, fields.Datetime.now()),
            attachments=[('%s.pdf' % job_sudo.name, pdf)],
            **({'token': access_token} if access_token else {}))

        query_string = '&message=sign_ok'

        return {
            'force_refresh': True,
            'redirect_url': job_sudo.get_portal_url(query_string=query_string),
        }