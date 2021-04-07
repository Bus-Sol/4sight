# -*- coding: utf-8 -*-
from odoo import models, fields, _, api
import logging
import json
from odoo.tools import config
import lxml.html

_logger = logging.getLogger(__name__)

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.model
    def print_pdf(self, options):

        return {
            'type': 'ir_actions_vat_report_download',
            'data': {'model': 'account.move.line',
                     'options': json.dumps(options),
                     'output_format': 'pdf',
                     }
        }

    def get_pdf(self, options, minimal_layout=True, **kwargs):

        if not config['test_enable']:
            self = self.with_context(commit_assetsbundle=True)

        base_url = self.env['ir.config_parameter'].sudo().get_param('report.url') or self.env[
            'ir.config_parameter'].sudo().get_param('web.base.url')

        line = []

        line_ids = self.env['account.move.line'].search(options,
                                                        order="vat_line_id asc, date desc, move_id asc")
        actual_vat_code = False
        dict_total_value_per_tax = {}
        dict_total_value = {'net_value':0, 'tax_value':0, 'gross_value': 0}

        for line_id in line_ids:
            dict_total_value['net_value'] += line_id.net_value
            dict_total_value['tax_value'] += line_id.tax_value
            dict_total_value['gross_value'] += line_id.gross_value

        line.append(['TOTAL', '', '','','', '%.2f' % dict_total_value['net_value'], '%.2f' % dict_total_value['tax_value'], '%.2f' % dict_total_value['gross_value']])

        for line_id in line_ids:
            if (str(str(line_id.vat_line_id.id)) + '_net' and str(line_id.vat_line_id.id) + '_tax' and str(line_id.vat_line_id.id) + '_gross') in dict_total_value_per_tax:
                dict_total_value_per_tax[str(line_id.vat_line_id.id) + '_net'] +=  line_id.net_value
                dict_total_value_per_tax[str(line_id.vat_line_id.id) + '_tax'] +=  line_id.tax_value
                dict_total_value_per_tax[str(line_id.vat_line_id.id) + '_gross'] +=  line_id.gross_value
            else:
                dict_total_value_per_tax[str(line_id.vat_line_id.id) + '_net'] = line_id.net_value
                dict_total_value_per_tax[str(line_id.vat_line_id.id) + '_tax'] = line_id.tax_value
                dict_total_value_per_tax[str(line_id.vat_line_id.id) + '_gross'] = line_id.gross_value

        for line_id in line_ids:
            if line_id.vat_line_id.id != actual_vat_code:
                line.append(
                    [line_id.vat_line_id.name,'',
                     '','','', '%.2f' % dict_total_value_per_tax[str(line_id.vat_line_id.id) + '_net'], '%.2f' % dict_total_value_per_tax[str(line_id.vat_line_id.id) + '_tax'], '%.2f' % dict_total_value_per_tax[str(line_id.vat_line_id.id) + '_gross']])

            actual_vat_code = line_id.vat_line_id.id

            line.append(
                [line_id.vat_line_id.name if line_id.vat_line_id.id != actual_vat_code else '', line_id.date, line_id.account_id.name,
                 line_id.move_id.name, line_id.name, '%.2f' % line_id.net_value, '%.2f' % line_id.tax_value, '%.2f' % line_id.gross_value])

        info_domain = {}
        date_start = False
        date_end = False
        for op in options:
            if type(op) is list:
                if op[0] == 'move_id.state' and op[2] == 'posted':
                    info_domain['state'] = 'posted'

                if op[0] == 'date' and op[1] == '>=':
                    if not date_start:
                        date_start = op[2]
                    else:
                        if date_start >= op[2]:
                            date_start = op[2]

                    info_domain['date_start'] = date_start

                if op[0] == 'date' and op[1] == '<=':
                    if not date_end:
                        date_end = op[2]
                    else:
                        if date_end <= op[2]:
                            date_end = op[2]

                    info_domain['date_end'] = date_end

        rcontext = {
            'mode': 'print',
            'base_url': base_url,
            'company': self.env.company,
            'lines': {'columns_header': ['', 'Date', 'Account', 'Journal', 'Label', 'Net Value', 'Tax Value', 'Gross Value'],
                      'lines': line, 'other_info': info_domain
                      }}

        body = self.env['ir.ui.view']._render_template(
            "l10n_mt.vat_template",
            values=dict(rcontext),
        )

        if minimal_layout:
            header = ''
            footer = self.env['ir.actions.report']._render_template("web.internal_layout", values=rcontext)
            spec_paperformat_args = {'data-report-margin-top': 10, 'data-report-header-spacing': 10}
            footer = self.env['ir.actions.report']._render_template("web.minimal_layout",
                                                                    values=dict(rcontext, subst=True, body=footer))
        else:
            rcontext.update({
                'css': '',
                'o': self.env.user,
                'res_company': self.env.company,
            })
            header = self.env['ir.actions.report']._render_template("web.external_layout", values=rcontext)
            header = header.decode('utf-8')  # Ensure that headers and footer are correctly encoded
            spec_paperformat_args = {}
            # Default header and footer in case the user customized web.external_layout and removed the header/footer
            headers = header.encode()
            footer = b''
            # parse header as new header contains header, body and footer
            try:
                root = lxml.html.fromstring(header)
                match_klass = "//div[contains(concat(' ', normalize-space(@class), ' '), ' {} ')]"

                for node in root.xpath(match_klass.format('header')):
                    headers = lxml.html.tostring(node)
                    headers = self.env['ir.actions.report']._render_template("web.minimal_layout",
                                                                             values=dict(rcontext, subst=True,
                                                                                         body=headers))

                for node in root.xpath(match_klass.format('footer')):
                    footer = lxml.html.tostring(node)
                    footer = self.env['ir.actions.report']._render_template("web.minimal_layout",
                                                                            values=dict(rcontext, subst=True,
                                                                                        body=footer))

            except lxml.etree.XMLSyntaxError:
                headers = header.encode()
                footer = b''
            header = headers

        landscape = False

        return self.env['ir.actions.report']._run_wkhtmltopdf(
            [body],
            header=header, footer=footer,
            landscape=True,
            specific_paperformat_args=spec_paperformat_args
        )