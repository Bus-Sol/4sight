# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import content_disposition, request
from odoo.addons.web.controllers.main import _serialize_exception
from odoo.tools import html_escape

import json

class VatReportController(http.Controller):

    @http.route('/vat_report_cy_download', type='http', auth='user', methods=['POST'], csrf=False)
    def get_report(self, model, options, output_format, token, **kw):
        uid = request.session.uid
        options = json.loads(options)
        cids = request.httprequest.cookies.get('cids', str(request.env.user.company_id.id))
        allowed_company_ids = [int(cid) for cid in cids.split(',')]
        report_obj = request.env['account.generic.tax.report'].with_user(uid).with_context(allowed_company_ids=allowed_company_ids)
        report_name = report_obj.get_report_filename(options)
        try:
            if output_format == 'pdf':
                response = request.make_response(
                    report_obj.get_pdf(options, vat_report_cy=True),
                    headers=[
                        ('Content-Type', report_obj.get_export_mime_type('pdf')),
                        ('Content-Disposition', content_disposition(report_name + '.pdf'))
                    ]
                )
            response.set_cookie('fileToken', token)
            return response
        except Exception as e:
            se = _serialize_exception(e)
            error = {
                'code': 200,
                'message': 'Odoo Server Error',
                'data': se
            }
            return request.make_response(html_escape(json.dumps(error)))