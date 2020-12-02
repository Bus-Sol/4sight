# -*- coding: utf-8 -*-
from odoo import models, fields, _, api
from odoo.addons.web.controllers.main import clean_action

class AccountReport(models.AbstractModel):
    _inherit = 'account.report'

    def open_action(self, options, domain):
        assert isinstance(domain, (list, tuple))
        domain += [('date', '>=', options.get('date').get('date_from')),
                   ('date', '<=', options.get('date').get('date_to'))]
        domain += [('account_group','=', '007')]
        if not options.get('all_entries'):
            domain += [('move_id.state', '=', 'posted')]

        ctx = self.env.context.copy()
        ctx.update({'search_default_account': 1, 'search_default_groupby_date': 1})

        action = self.env.ref('account.action_move_line_select_tax_audit').read()[0]
        action = clean_action(action)
        action['domain'] = domain
        action['context'] = ctx
        return action


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    tax_value = fields.Monetary(string='Tax Value',compute='get_tax_value',currency_field='company_currency_id',store=True)
    net_value = fields.Monetary(string='Net Value',compute='get_net_value',currency_field='company_currency_id',store=True)
    gross_value = fields.Monetary(string='Gross Value',compute='get_gross_value',currency_field='company_currency_id',store=True)
    account_group = fields.Char(compute='get_account_group_name',string='Account Group',store=True)

    @api.depends('tax_base_amount')
    def get_tax_value(self):

        for record in self:
            record.tax_value = 0
            for tag in record.tag_ids:
                tag_amount = (tag.tax_negate and -1 or 1) * (record.move_id.is_inbound() and -1 or 1) * record.balance
                if tag_amount:
                    record.tax_value = tag_amount

    @api.depends('tax_base_amount')
    def get_net_value(self):

        for record in self:
            record.net_value = 0
            if record.tax_base_amount:
                if record.move_id.type in ['out_refund','in_refund']:
                    record.net_value = record.tax_base_amount * -1
                else:
                    record.net_value = record.tax_base_amount

    @api.depends('tax_base_amount')
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