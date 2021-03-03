# -*- coding: utf-8 -*-
from odoo import models, _, api, fields


class AccountChartTemplate(models.Model):

    _inherit = 'account.chart.template'

    def _create_bank_journals(self, company, acc_template_ref):

        if not self.name == 'MT Tax and Account Chart Template (by 4Sight)':
            self.ensure_one()
            bank_journals = self.env['account.journal']
            # Create the journals that will trigger the account.account creation
            for acc in self._get_payment_bank_journals_data():
                bank_journals += self.env['account.journal'].create({
                    'name': acc['acc_name'],
                    'type': acc['account_type'],
                    'company_id': company.id,
                    'currency_id': acc.get('currency_id', self.env['res.currency']).id,
                    'sequence': 10
                })
            return bank_journals
        else:
            return False

    def _prepare_all_journals(self, acc_template_ref, company, journals_dict=None):
        res = super(AccountChartTemplate, self)._prepare_all_journals(
            acc_template_ref, company, journals_dict=journals_dict)
        if not self == self.env.ref('l10n_mt.l10n_mt'):
            return res
        account_4000 = acc_template_ref.get(self.env.ref('l10n_mt.4000').id)
        account_6900 = acc_template_ref.get(self.env.ref('l10n_mt.6900').id)
        account_7906 = acc_template_ref.get(self.env.ref('l10n_mt.7906').id)
        account_1200 = acc_template_ref.get(self.env.ref('l10n_mt.1200').id)
        account_1230 = acc_template_ref.get(self.env.ref('l10n_mt.1230').id)
        journals = self.env['account.journal'].search([])
        for j in journals:
            j.unlink()
        res = [{
            'type': 'sale',
            'name': 'Customer Invoices',
            'code': 'INV',
            'company_id': company.id,
            'payment_credit_account_id': account_4000,
            'payment_debit_account_id': account_4000,
        },
            {
                'type': 'purchase',
                'name': 'Vendor Bills',
                'code': 'BILL',
                'company_id': company.id,
                'payment_credit_account_id': account_6900,
                'payment_debit_account_id': account_6900,
            },
            {
                'type': 'general',
                'name': 'Miscellaneous Operations',
                'code': 'MISC',
                'company_id': company.id,
                'payment_credit_account_id': account_7906,
                'payment_debit_account_id': account_7906,
            },
            {
            'type': 'general',
            'name': 'Exchange Difference',
            'code': 'EXCH',
            'company_id': company.id,
            'payment_credit_account_id': account_7906,
            'payment_debit_account_id': account_7906,
        },
            {
                'type': 'bank',
                'name': 'Bank',
                'code': 'BNK1',
                'company_id': company.id,
                'bank_statements_source': 'file_import',
                'payment_credit_account_id': account_1200,
                'payment_debit_account_id': account_1200,
            },
            {
                'type': 'cash',
                'name': 'Petty Cash',
                'code': 'CSH1',
                'company_id': company.id,
                'payment_credit_account_id': account_1230,
                'payment_debit_account_id': account_1230,
            }
        ]
        return res

class AccountAccountTemplate(models.Model):
    _inherit = "account.account.template"

    mt_group_id = fields.Many2one('account.group')
