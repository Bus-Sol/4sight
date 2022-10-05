# -*- coding: utf-8 -*-
import logging
import json
from odoo.tools import config
from odoo import api, models, fields, _

_logger = logging.getLogger(__name__)

class AccountReportVatCy(models.AbstractModel):

    _description = "Vat Report CY"
    _inherit = "account.generic.tax.report"

    def _get_reports_buttons(self):
        res = super(AccountReportVatCy, self)._get_reports_buttons()
        if self.env.user.has_group('account.group_account_user') and self.env.company.country_code =="CY":
            res.append({'name': _('Print VAT (CY)'), 'sequence': 3, 'action': 'print_cy_pdf', 'file_export_type': _('PDF')})
        return res

    def print_cy_pdf(self, options):
        return {
            'type': 'ir_actions_vat_report_cy_download',
            'data': {'model': "account.generic.tax.report",
                     'options': json.dumps(options),
                     'output_format': 'pdf',
                     }
        }

    def extract_fractional_part(self, lines_data):
        for k, v in lines_data.items():
            split_value = str(v).split('.')
            if split_value:
                if len(split_value) > 1:
                    format_cent = "00"
                    if split_value[1] !=0:
                        if len(split_value[1]) == 1:
                            format_cent = split_value[1] + "0"
                        else:
                            format_cent = split_value[1][:2]
                    lines_data[k] = (int(split_value[0]),format_cent)
                else:
                    lines_data[k] = (int(split_value[0]), '00')
    def get_pdf(self, options, minimal_layout=True, **kwargs ):
        if kwargs.get('vat_report_cy', False):
            if not config['test_enable']:
                self = self.with_context(commit_assetsbundle=True)
            lines = self._get_lines(options)
            _logger.info('Standard Lines**** %s', lines)
            new_lines = []
            lines_data = {}
            for line in lines:
                if "total_" in str(line['id']):
                    new_lines.append(line)
            _logger.info('NEw Lines**** %s', new_lines)
            lines_data['1'] = new_lines[0]['columns'][0]['balance']
            lines_data['2'] = new_lines[1]['columns'][0]['balance']
            lines_data['3'] = new_lines[2]['columns'][0]['balance']
            lines_data['4'] = new_lines[3]['columns'][0]['balance']
            lines_data['5'] = new_lines[4]['columns'][0]['balance']
            lines_data['6'] = new_lines[5]['columns'][0]['balance']
            lines_data['7'] = new_lines[6]['columns'][0]['balance']
            lines_data['8a'] = new_lines[7]['columns'][0]['balance']
            lines_data['8b'] = new_lines[8]['columns'][0]['balance']
            lines_data['9'] = new_lines[9]['columns'][0]['balance']
            lines_data['10'] = new_lines[10]['columns'][0]['balance']
            lines_data['11a'] = new_lines[11]['columns'][0]['balance']
            lines_data['11b'] = new_lines[12]['columns'][0]['balance']
            self.extract_fractional_part(lines_data)
            date_from = options['date']['date_from']
            date_to = options['date']['date_to']
            base_url = self.env['ir.config_parameter'].sudo().get_param('report.url') or self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            rcontext = {
                'mode': 'print',
                'base_url': base_url,
                'company': self.env.company,
                'options': options,
                'date_from': date_from,
                'date_to': date_to,
                'lines': lines_data
            }
            body = self.env['ir.ui.view']._render_template("vat_report_cy.print_template", values=dict(rcontext))
            spec_paperformat_args = {'data-report-margin-top': 5, 'data-report-margin-bottom': 7,
                                     'data-report-header-spacing': 10}
            if minimal_layout:
                header = ''
            landscape = False
            self.env.context.update({'print_vat':True})
            return self.env['ir.actions.report']._run_wkhtmltopdf(
                [body],
                header=header,
                landscape=landscape,
                specific_paperformat_args=spec_paperformat_args
            )
        return super(AccountReportVatCy, self).get_pdf(options=options)

class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def get_paperformat(self, **kwargs):
        # force the right format (euro/A4) when sending letters, only if we are not using the l10n_DE layout
        res = super(IrActionsReport, self).get_paperformat()
        if not self.env.context:
            paper_format_id = self.env.ref('vat_report_cy.paperformat_vat_cy').id
            paperformat_id = self.env['report.paperformat'].browse(paper_format_id)
            return paperformat_id
        return res
