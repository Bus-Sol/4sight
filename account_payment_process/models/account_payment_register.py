# -*- coding: utf-8 -*-
import sys

from odoo import models, fields, _, api
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    invoice_line_ids = fields.One2many('account.payment.register.line', 'inv_line_id', string="Move lines")
    edit_amount = fields.Boolean('Edit Amount(s)', default=False)
    post_payment = fields.Boolean('Post Payment', default=True)
    amount_total = fields.Monetary('Total', readonly=True, compute='_amount_all')

    @api.onchange('edit_amount')
    def onchange_edit_amount(self):
        if self.edit_amount:
            self.group_payment = False


    @api.depends('invoice_line_ids.amount')
    def _amount_all(self):

        for payments in self:
            amount_total = 0.0
            for line in payments.invoice_line_ids:
                amount_total += line.amount
            payments.update({
                'amount_total': amount_total,
            })

    @api.model
    def default_get(self, fields_list):
        # OVERRIDE
        res = super().default_get(fields_list)
        if 'invoice_line_ids' in fields_list:
            if self._context.get('active_model') == 'account.move':
                lines = self.env['account.move'].browse(self._context.get('active_ids', [])).line_ids
            elif self._context.get('active_model') == 'account.move.line':
                lines = self.env['account.move.line'].browse(self._context.get('active_ids', []))
            else:
                raise UserError(_(
                    "The register payment wizard should only be called on account.move or account.move.line records."
                ))
            inv_line_list = []
            line_ids = self.env['account.move.line'].browse(res['line_ids'][0][2])
            for line in line_ids:
                inv_line_list.append((0, 0, {
                    'name': line.name,
                    'date': line.date,
                    'amount': line.amount_residual,
                    'previous_amount': line.amount_residual,
                    'ref_move_copy': line.name,
                }))
            res['invoice_line_ids'] = inv_line_list

        return res

    def _create_payments(self):
        self.ensure_one()
        batches = self._get_batches()
        edit_mode = self.can_edit_wizard and (len(batches[0]['lines']) == 1 or self.group_payment)

        to_reconcile = []
        if edit_mode:
            payment_vals = self._create_payment_vals_from_wizard('batch_result')
            payment_vals_list = [payment_vals]
            to_reconcile.append(batches[0]['lines'])
        else:
            # Don't group payments: Create one batch per move.
            if not self.group_payment:
                new_batches = []
                for batch_result in batches:
                    for line in batch_result['lines']:
                        new_batches.append({
                            **batch_result,
                            'lines': line,
                        })
                batches = new_batches

            payment_vals_list = []
            for batch_result in batches:
                payment_vals_list.append(self._create_payment_vals_from_batch(batch_result))
                to_reconcile.append(batch_result['lines'])
        if self.edit_amount:
            for payment in payment_vals_list:
                payment['copy_ref'] = payment['ref']
            for payment in payment_vals_list:
                for inv_line_id in self.invoice_line_ids:

                    if inv_line_id['ref_move_copy'] == payment['copy_ref']:
                        payment['amount'] = abs(inv_line_id['amount'])
                        payment['ref'] = inv_line_id['name']
            for payment in payment_vals_list:
                payment.pop('copy_ref', None)
        _logger.info('Vals : %s', payment_vals_list)

        payments = self.env['account.payment'].create(payment_vals_list)

        # If payments are made using a currency different than the source one, ensure the balance match exactly in
        # order to fully paid the source journal items.
        # For example, suppose a new currency B having a rate 100:1 regarding the company currency A.
        # If you try to pay 12.15A using 0.12B, the computed balance will be 12.00A for the payment instead of 12.15A.
        if edit_mode:
            for payment, lines in zip(payments, to_reconcile):
                # Batches are made using the same currency so making 'lines.currency_id' is ok.
                if payment.currency_id != lines.currency_id:
                    liquidity_lines, counterpart_lines, writeoff_lines = payment._seek_for_lines()
                    source_balance = abs(sum(lines.mapped('amount_residual')))
                    payment_rate = liquidity_lines[0].amount_currency / liquidity_lines[0].balance
                    source_balance_converted = abs(source_balance) * payment_rate

                    # Translate the balance into the payment currency is order to be able to compare them.
                    # In case in both have the same value (12.15 * 0.01 ~= 0.12 in our example), it means the user
                    # attempt to fully paid the source lines and then, we need to manually fix them to get a perfect
                    # match.
                    payment_balance = abs(sum(counterpart_lines.mapped('balance')))
                    payment_amount_currency = abs(sum(counterpart_lines.mapped('amount_currency')))
                    if not payment.currency_id.is_zero(source_balance_converted - payment_amount_currency):
                        continue

                    delta_balance = source_balance - payment_balance

                    # Balance are already the same.
                    if self.company_currency_id.is_zero(delta_balance):
                        continue

                    # Fix the balance but make sure to peek the liquidity and counterpart lines first.
                    debit_lines = (liquidity_lines + counterpart_lines).filtered('debit')
                    credit_lines = (liquidity_lines + counterpart_lines).filtered('credit')

                    payment.move_id.write({'line_ids': [
                        (1, debit_lines[0].id, {'debit': debit_lines[0].debit + delta_balance}),
                        (1, credit_lines[0].id, {'credit': credit_lines[0].credit + delta_balance}),
                    ]})
        if self.post_payment:
            payments.action_post()

        domain = [('account_type', 'in', ('asset_receivable', 'liability_payable')), ('reconciled', '=', False)]
        for payment, lines in zip(payments, to_reconcile):

            # When using the payment tokens, the payment could not be posted at this point (e.g. the transaction failed)
            # and then, we can't perform the reconciliation.
            if payment.state != 'posted':
                continue

            payment_lines = payment.line_ids.filtered_domain(domain)
            for account in payment_lines.account_id:
                (payment_lines + lines)\
                    .filtered_domain([('account_id', '=', account.id), ('reconciled', '=', False)])\
                    .reconcile()

        return payments


class AccountPaymentRegisterLine(models.TransientModel):
    _name = 'account.payment.register.line'


    inv_line_id = fields.Many2one('account.payment.register', required=True, ondelete='cascade')
    name = fields.Text('Memo')
    amount = fields.Monetary('Amount')
    previous_amount = fields.Monetary('Previous Amount')
    date = fields.Date('Date')
    ref_move_copy = fields.Char('Ref Move Copy')
    currency_id = fields.Many2one(string="Currency", related='company_id.currency_id', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True, default=lambda self: self.env.company)

    @api.constrains('amount')
    def check_amount_value(self):
        for line in self:
            if line.amount and line.inv_line_id.payment_type == 'inbound':
                if line.amount > line.previous_amount:
                    raise UserError(_("You cannot set an amount higher than its original."))

