# -*- coding: utf-8 -*-
from odoo import models, fields, _, api
import logging

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit='account.move'


    @api.onchange('line_ids','invoice_line_ids')
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

    tax_value = fields.Monetary(string='Tax Value',compute='get_tax_value',currency_field='company_currency_id',store=True)
    net_value = fields.Monetary(string='Net Value',compute='get_net_value',currency_field='company_currency_id',store=True)
    gross_value = fields.Monetary(string='Gross Value',compute='get_gross_value',currency_field='company_currency_id',store=True)
    account_group = fields.Char(compute='get_account_group_name',string='Account Group',store=True)
    vat_line_id = fields.Many2one('account.tax', string='VAT', store=True)

    @api.depends('tax_base_amount', 'tax_audit')
    def get_tax_value(self):

        for record in self:
            record.tax_value = 0
            record.tax_value = record.move_id.amount_tax

    @api.depends('tax_base_amount','tax_audit')
    def get_net_value(self):

        for record in self:
            record.net_value = 0
            if record.tax_base_amount:
                if record.move_id.type in ['out_refund','in_refund']:
                    record.net_value = record.tax_base_amount * -1
                else:
                    record.net_value = record.tax_base_amount
            else:
                record.net_value = record.move_id.amount_untaxed

    @api.depends('net_value','tax_value')
    def get_gross_value(self):
        for record in self:
            record.gross_value = 0
            if record.tax_value and record.net_value:
                record.gross_value = record.net_value + record.tax_value

    @api.depends('account_id')
    def get_account_group_name(self):

        for record in self:
            record.account_group = ''
            if record.account_id:
                record.account_group = record.account_id.group_id.code_prefix