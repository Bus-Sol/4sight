# -*- coding: utf-8 -*-
from odoo import models, fields, _, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    def cron_compute_field(self):
        for line in self.env['account.move'].search([('invoice_line_ids','!=',False)]).invoice_line_ids:
            if line:
                if line.tax_ids:
                    if line.move_id.move_type in ['out_refund', 'in_refund']:
                        line.net_value = line.price_subtotal * -1
                        line.tax_value = (line.price_total - line.price_subtotal) * -1
                    else:
                        line.net_value = line.price_subtotal
                        line.tax_value = line.price_total - line.price_subtotal
                    line.gross_value = line.net_value + line.tax_value
                    line.vat_line_id = line.tax_ids.ids[0]

        for r in self.env['account.move'].search([('move_type', 'in', ['in_invoice','out_invoice'])]):

            exist_line = False
            total = 0
            for rec in r.env['account.move.line'].search([('move_id', '=', r.id)]):
                if rec.is_vat_round:
                    exist_line = True

            for rec in r.invoice_line_ids:
                total += round(rec.tax_value,2)

            diff = r.amount_by_group[0][1] - total if r.amount_by_group else 0
            if round(diff,2) != 0:
                if not exist_line:
                    line_id = r.env['account.move.line'].create({
                        'move_id': r.id,
                        'exclude_from_invoice_tab': True,
                        'is_vat_round': True,
                        'tax_value': diff,
                        'gross_value': diff,
                        'vat_line_id': r.invoice_line_ids.filtered(lambda line: line.vat_line_id != False).mapped('vat_line_id')[0].id,
                        'name': 'VAT Rounding',
                        'account_id': r.invoice_line_ids.filtered(lambda line: line.account_id != False).mapped('account_id')[0].id
                    })
                else:
                    line = r.env['account.move.line'].search(
                        [('move_id', '=', r.id), ('is_vat_round', '=', True)])
                    line.tax_value = line.gross_value = diff
                    line.vat_line_id = r.invoice_line_ids.filtered(lambda line: line.vat_line_id != False).mapped('vat_line_id')[0].id

    def write(self, vals):
        res = super(AccountMove, self).write(vals)
        for lines in self:
            if lines.invoice_line_ids:
                for record in lines.invoice_line_ids:
                    if record.tax_ids:
                        record.vat_line_id = record.tax_ids.ids[0]
                    else:
                        record.vat_line_id = False
                    if record.move_id.move_type in ['out_refund', 'in_refund']:
                        record.net_value = record.price_subtotal * -1
                        record.tax_value = (record.price_total - record.price_subtotal) * -1
                    else:
                        record.net_value = record.price_subtotal
                        record.tax_value = record.price_total - record.price_subtotal
                    record.gross_value = record.net_value + record.tax_value

                exist_line = False
                total = 0
                for rec in self.env['account.move.line'].search([('move_id', '=', lines.id)]):
                    if rec.is_vat_round:
                        exist_line = True

                for rec in lines.invoice_line_ids:
                    total += round(rec.tax_value,2)

                ## changes should be done here###
                if lines.move_type in ['out_refund', 'in_refund']:
                    diff = (lines.amount_by_group[0][1] - abs(total)) * -1 if lines.amount_by_group else 0
                else:
                    diff = lines.amount_by_group[0][1] - total if lines.amount_by_group else 0
                if round(diff,2) != 0:
                    if not exist_line:
                        line_id = self.env['account.move.line'].create({
                            'move_id': lines.id,
                            'exclude_from_invoice_tab': True,
                            'is_vat_round': True,
                            'tax_value': diff,
                            'gross_value': diff,
                            'vat_line_id': lines.invoice_line_ids.filtered(lambda line: line.vat_line_id != False).mapped('vat_line_id')[0].id,
                            'name': 'VAT Rounding',
                            'account_id': lines.invoice_line_ids.filtered(lambda line: line.account_id != False).mapped('account_id')[0].id
                        })
                    else:
                        line = self.env['account.move.line'].search([('move_id','=',lines.id),('is_vat_round','=',True)])
                        line.tax_value = line.gross_value = diff
                        line.vat_line_id = lines.invoice_line_ids.filtered(lambda line: line.vat_line_id != False).mapped('vat_line_id')[0].id
                else:
                    if exist_line:
                        move_line = self.env['account.move.line'].search([('move_id','=', lines.id),('is_vat_round','=',True)])
                        if move_line: self.env.cr.execute(
            'DELETE from account_move_line WHERE id=%s',(move_line.id,))
        return res


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    tax_value = fields.Monetary(string='Tax Value', currency_field='company_currency_id')
    net_value = fields.Monetary(string='Net Value', currency_field='company_currency_id')
    gross_value = fields.Monetary(string='Gross Value', currency_field='company_currency_id')
    account_group = fields.Char(compute='get_account_group_name', string='Account Group', store=True)
    vat_line_id = fields.Many2one('account.tax', string='VAT')
    is_vat_round = fields.Boolean('Is VAT Round', default=False)


    @api.depends('account_id')
    def get_account_group_name(self):

        for record in self:
            record.account_group = ''
            if record.account_id:
                record.account_group = record.account_id.group_id.code_prefix_start