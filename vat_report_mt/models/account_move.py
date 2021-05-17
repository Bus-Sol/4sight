# -*- coding: utf-8 -*-
from odoo import models, fields, _, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    def cron_compute_field(self):

        for line in self.env['account.move'].search([]).invoice_line_ids:
            line.vat_line_id = False
            if line.tax_ids:
                if line.move_id.move_type in ['out_refund','in_refund']:
                    line.net_value = line.price_subtotal * -1
                    line.tax_value = (line.price_total - line.price_subtotal) * -1
                else:
                    line.net_value = line.price_subtotal
                    line.tax_value = line.price_total - line.price_subtotal
                line.vat_line_id = line.tax_ids.ids[0]



class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    tax_value = fields.Monetary(string='Tax Value', compute='get_tax_value', currency_field='company_currency_id',
                                store=True)
    net_value = fields.Monetary(string='Net Value', compute='get_tax_value', currency_field='company_currency_id',
                                store=True)
    gross_value = fields.Monetary(string='Gross Value', compute='get_gross_value', currency_field='company_currency_id',
                                  store=True)
    account_group = fields.Char(compute='get_account_group_name', string='Account Group', store=True)
    vat_line_id = fields.Many2one('account.tax', string='VAT', compute='get_vat_line', store=True)


    @api.depends('tax_ids')
    def get_vat_line(self):
        for rec in self:
            if rec.tax_ids:
                rec.vat_line_id = rec.tax_ids.ids[0]
            else:
                rec.vat_line_id = False

    @api.depends('price_subtotal')
    def get_tax_value(self):

        for record in self:
            if record.move_id.move_type in ['out_refund', 'in_refund']:
                record.net_value = record.price_subtotal * -1
                record.tax_value = (record.price_total - record.price_subtotal) * -1
            else:
                record.net_value = record.price_subtotal
                record.tax_value = record.price_total - record.price_subtotal


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