# -*- coding: utf-8 -*-

{
    'name': 'MT - Accounting',
    'version': '1.0',
    'category': 'Localization',
    'description': """
This is an MT Odoo localisation necessary to run Odoo accounting for MT SME's with:
=================================================================================================
    - a CT600-ready chart of accounts
    - VAT100-ready tax structure
    - InfoLogic MT counties listing
    - a few other adaptations""",
    'author': '4Sight Group',
    'website': 'https://www.odoo.com/page/accounting',
    'depends': [
        'account',
        'base_iban',
        'base_vat',
        'account_reports',
    ],
    'data': [
        'data/l10n_mt_chart_data.xml',
        'data/account_group_data.xml',
        'data/account.account.template.csv',
        'data/account.chart.template.csv',
        'data/account.tax.group.csv',
        'data/account_tax_report_data.xml',
        'data/account_tax_data.xml',
        'data/account_chart_template_data.xml',
        'data/account_reconcile_data.xml',
        'data/account_payment_term_data.xml',
        'views/account_vat_report.xml',
    ],
    'demo' : [
    ],
    'pre_init_hook' :  'pre_init_check',
}
