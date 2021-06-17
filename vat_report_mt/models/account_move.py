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
                    line.vat_line_id = line.tax_ids.ids[0]


        for r in self.env['account.move'].search([('move_type', 'in', ['in_invoice','out_invoice'])]):

            exist_line = False
            total = 0
            for rec in r.env['account.move.line'].search([('move_id', '=', r.id)]):
                if rec.is_vat_round:
                    exist_line = True

            for rec in r.invoice_line_ids:
                total += rec.tax_value

            diff = r.amount_by_group[0][1] - total if r.amount_by_group else 0
            if diff != 0:
                if not exist_line:
                    line_id = r.env['account.move.line'].create({
                        'move_id': r.id,
                        'exclude_from_invoice_tab': True,
                        'is_vat_round': True,
                        'name': 'VAT Rounding',
                        ''
                        'account_id': r.invoice_line_ids[0].account_id.id
                    })
                    r.env.cr.execute(
                        """UPDATE account_move_line SET tax_value = %s, gross_value = %s WHERE id = %s """ % (diff,diff, line_id.id))
                    r.env.cr.execute("""UPDATE account_move_line SET vat_line_id = %s WHERE id = %s """ % (
                    r.invoice_line_ids[0].vat_line_id.id, line_id.id))
                else:
                    r.env.cr.execute(
                        """UPDATE account_move_line SET tax_value = %s,  gross_value = %s WHERE move_id = %s AND is_vat_round = TRUE """ % (
                        diff, diff, r.id))
                    r.env.cr.execute("""UPDATE account_move_line SET vat_line_id = %s WHERE move_id = %s AND is_vat_round = TRUE """ % (
                    r.invoice_line_ids[0].vat_line_id.id, r.id))

    def write(self, vals):

        rslt = super(AccountMove, self).write(vals)
        exist_line = False
        total = 0
        for rec in self.env['account.move.line'].search([('move_id', '=', self.id)]):
            if rec.is_vat_round:
                exist_line = True

        for rec in self.invoice_line_ids:
            total += rec.tax_value

        diff = self.amount_by_group[0][1] - total if self.amount_by_group else 0
        if diff != 0:
            if not exist_line:
                line_id = self.env['account.move.line'].create({
                    'move_id': self.id,
                    'exclude_from_invoice_tab': True,
                    'is_vat_round': True,
                    'name': 'VAT Rounding',
                    'account_id': self.invoice_line_ids[0].account_id.id
                })
                self.env.cr.execute(
                    """UPDATE account_move_line SET tax_value = %s, gross_value = %s WHERE id = %s """ % (diff, diff, line_id.id))
                self.env.cr.execute("""UPDATE account_move_line SET vat_line_id = %s WHERE id = %s """ % (
                self.invoice_line_ids[0].vat_line_id.id, line_id.id))
            else:
                self.env.cr.execute(
                    """UPDATE account_move_line SET tax_value = %s, gross_value = %s WHERE move_id = %s AND is_vat_round = TRUE """ % (
                    diff, diff, self.id))
                self.env.cr.execute("""UPDATE account_move_line SET vat_line_id = %s WHERE move_id = %s AND is_vat_round = TRUE """ % (
                self.invoice_line_ids[0].vat_line_id.id, self.id))

        return rslt


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
    is_vat_round = fields.Boolean('Is VAT Round', default=False)

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