# -*- coding: utf-8 -*-

{
    'name': 'MT - Accounting',
    'version': '1.0',
    'category': 'Accounting/Localizations/Account Charts',
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
        'account_followup',
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
        'report/vat_report_template.xml',
        'views/assets.xml',
        'views/account_vat_report.xml',
        'views/account_followups.xml',
    ],
    'qweb': [
        'static/src/xml/base.xml',
        ],
    'demo' : [
    ],
    'pre_init_hook' :  'pre_init_check',
}
