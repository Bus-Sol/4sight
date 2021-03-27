# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import content_disposition, request
from odoo.addons.web.controllers.main import _serialize_exception
from odoo.tools import html_escape

import json


class VatReportController(http.Controller):

    @http.route('/account_move_line', type='http', auth='user', methods=['POST'], csrf=False)
    def get_report(self, model, options, output_format, token, financial_id=None, **kw):
        uid = request.session.uid
        account_report_model = request.env['account.move.line']
        options = json.loads(options)
        cids = request.httprequest.cookies.get('cids', str(request.env.user.company_id.id))
        allowed_company_ids = [int(cid) for cid in cids.split(',')]
        report_obj = request.env[model].with_user(uid).with_context(allowed_company_ids=allowed_company_ids)
        if financial_id and financial_id != 'null':
            report_obj = report_obj.browse(int(financial_id))
        report_name = 'VAT Report'
        try:
            if output_format == 'xlsx':
                response = request.make_response(
                    None,
                    headers=[
                        ('Content-Type', account_report_model.get_export_mime_type('xlsx')),
                        ('Content-Disposition', content_disposition(report_name + '.xlsx'))
                    ]
                )
                response.stream.write(report_obj.get_xlsx(options))
            if output_format == 'pdf':
                response = request.make_response(
                    report_obj.get_pdf(options),
                    headers=[
                        ('Content-Type','application/pdf'),
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