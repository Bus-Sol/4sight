# coding: utf-8
import logging
from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    def auto_create_bank_statement(self):

        this_month = fields.Date.today().month
        this_year = fields.Date.today().year
        account_bank_stat_id = False
        msg = ''

        acquirer_id = self.env['payment.acquirer'].search(
            [('provider', '=', 'viva'), ('company_id', '=', self.company_id.id)])
        if acquirer_id:
            transactions = self.env['payment.transaction'].search(
                [('acquirer_id', '=', acquirer_id.id), ('state', '=', 'done')])
            account_bank_stat_ids = self.env['account.bank.statement'].search([('journal_id', '=', self.id)])
            for statement_id in account_bank_stat_ids:
                if statement_id.date.month == this_month and statement_id.date.year == this_year and statement_id.company_id == self.company_id:
                    account_bank_stat_id = statement_id
                    msg += 'A bank statement already exists for this month'
                    break

            ##### create bank statement if account_bank_stat_id = False ###
            if not account_bank_stat_id:
                bank_statement = self.env['account.bank.statement'].create({
                    'journal_id': self.id,
                    'company_id': self.company_id.id,
                    'date': fields.Date.today()
                })
                account_bank_stat_id = bank_statement
                msg += 'A bank statement has been created'

            new_line = False
            for tx in transactions:
                #### check for transaction id ( to be displayed in reference field of the line_ids
                if tx.date.month == this_month and tx.date.year == this_year:
                    if not self.env['account.bank.statement.line'].search([('viva_trx','=',tx.acquirer_reference)]):

                        account_bank_stat_id.write({'line_ids': [(0, 0, {
                            'date': tx.date,
                            'payment_ref': tx.payment_id.name if tx.payment_id else tx.reference,
                            'partner_id': tx.partner_id.id,
                            'viva_trx': tx.acquirer_reference,
                            'amount': tx.amount,
                        })]})
                        new_line = True

            account_bank_stat_id.balance_end_real = account_bank_stat_id.balance_end
            if new_line:
                msg += ', some transactions have been added.'
            else:
                msg += ', no new transactions yet, you are up-to-date.'

            notification = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': ('Synchronize Transactions'),
                    'message': msg,
                    'type': 'success',
                    'sticky': True,
                },
            }
            return notification