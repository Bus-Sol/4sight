# -*- coding: utf-8 -*-
from odoo import models, fields, _, api
import logging
import json
from odoo.tools import config
import lxml.html

_logger = logging.getLogger(__name__)


class AccountAccount(models.Model):
    _inherit = "account.account"

    mt_group_id = fields.Many2one('account.group', string='Mt Group')


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    def cron_compute_field(self):
        for line in self.env['account.move'].search([]).line_ids:
            line.vat_line_id = False
            if line.tax_ids:
                for taxe in line.tax_ids:
                    if taxe.amount == 0.0:
                        line.vat_line_id = taxe.ids[0]

            if line.tax_line_id:
                line.vat_line_id = line.tax_line_id

    @api.onchange('line_ids', 'invoice_line_ids')
    def onchange_vat_line_id(self):
        for line in self.line_ids:
            line.vat_line_id = False
            if line.tax_ids:
                for taxe in line.tax_ids:
                    if taxe.amount == 0.0:
                        line.vat_line_id = taxe.ids[0]

            if line.tax_line_id:
                line.vat_line_id = line.tax_line_id


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    tax_value = fields.Monetary(string='Tax Value', compute='get_tax_value', currency_field='company_currency_id',
                                store=True)
    net_value = fields.Monetary(string='Net Value', compute='get_net_value', currency_field='company_currency_id',
                                store=True)
    gross_value = fields.Monetary(string='Gross Value', compute='get_gross_value', currency_field='company_currency_id',
                                  store=True)
    account_group = fields.Char(compute='get_account_group_name', string='Account Group', store=True)
    vat_line_id = fields.Many2one('account.tax', string='VAT', store=True)

    @api.depends('tax_base_amount', 'tax_audit')
    def get_tax_value(self):

        for record in self:
            record.tax_value = 0
            record.tax_value = record.move_id.amount_tax

    @api.depends('tax_base_amount', 'tax_audit')
    def get_net_value(self):

        for record in self:
            record.net_value = 0
            if record.tax_base_amount:
                if record.move_id.move_type in ['out_refund', 'in_refund']:
                    record.net_value = record.tax_base_amount * -1
                else:
                    record.net_value = record.tax_base_amount
            else:
                if record.move_id.move_type in ['out_refund', 'in_refund']:
                    record.net_value = record.price_subtotal * -1
                else:
                    record.net_value = record.price_subtotal

    @api.depends('net_value', 'tax_value')
    def get_gross_value(self):
        for record in self:
            record.gross_value = record.net_value + record.tax_value

    @api.depends('account_id')
    def get_account_group_name(self):

        for record in self:
            record.account_group = ''
            if record.account_id:
                record.account_group = record.account_id.group_id.code_prefix_start

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
        for line_id in line_ids:
            line.append(
                [line_id.vat_line_id.name if line_id.vat_line_id.name != actual_vat_code else '', line_id.date,
                 line_id.move_id.name, line_id.net_value, line_id.tax_value, line_id.gross_value])

            actual_vat_code = line_id.vat_line_id.name

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
            'lines': {'columns_header': ['', 'Date', 'Journal', 'Net Value', 'Tax Value', 'Gross Value'],
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
            landscape=landscape,
            specific_paperformat_args=spec_paperformat_args
        )