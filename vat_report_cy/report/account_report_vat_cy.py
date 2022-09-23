# -*- coding: utf-8 -*-

import json
from odoo.tools import config
from odoo import api, models, fields, _

class AccountReportVatCy(models.AbstractModel):

    _description = "Vat Report CY"
    _inherit = "account.generic.tax.report"

    def _get_reports_buttons(self):
        res = super(AccountReportVatCy, self)._get_reports_buttons()
        if self.env.user.has_group('account.group_account_user'):
            res.append({'name': _('Print VAT (CY)'), 'sequence': 3, 'action': 'print_pdf', 'file_export_type': _('PDF')})
        return res

    def print_pdf(self, options):
        return {
            'type': 'ir_actions_vat_report_cy_download',
            'data': {'model': "account.generic.tax.report",
                     'options': json.dumps(options),
                     'output_format': 'pdf',
                     }
        }

    def get_pdf(self, options, minimal_layout=True, **kwargs ):

        if not config['test_enable']:
            self = self.with_context(commit_assetsbundle=True)
        print(kwargs)
        base_url = self.env['ir.config_parameter'].sudo().get_param('report.url') or self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        rcontext = {
            'mode': 'print',
            'base_url': base_url,
            'company': self.env.company,
            'options': options
        }
        body = self.env['ir.ui.view']._render_template("vat_report_cy.print_template", values=dict(rcontext))
        spec_paperformat_args = {'data-report-margin-top': 5, 'data-report-margin-bottom': 7,
                                 'data-report-header-spacing': 10}
        if minimal_layout:
            header = ''
            # footer = self.env['ir.actions.report']._render_template("web.internal_layout", values=rcontext)
            # footer = self.env['ir.actions.report']._render_template("web.minimal_layout", values=dict(rcontext, subst=True, body=footer))
        # footer = self.env['ir.actions.report']._render_template("web.minimal_layout", values={"paperformat_id":6})
        landscape = False
        return self.env['ir.actions.report']._run_wkhtmltopdf(
            [body],
            header=header,
            landscape=landscape,
            specific_paperformat_args=spec_paperformat_args
        )

    def get_report_filename(self,):
        """The name that will be used for the file when downloading pdf,xlsx,..."""
        return _("Vat Report CY")

class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'


    def get_paperformat(self):
        # force the right format (euro/A4) when sending letters, only if we are not using the l10n_DE layout
        res = super(IrActionsReport, self).get_paperformat()
        paperformat_id = self.env['report.paperformat'].browse(6)
        return paperformat_id

