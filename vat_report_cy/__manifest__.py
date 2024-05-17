# -*- coding: utf-8 -*-

{
    'name': 'VAT Report CY',
    'version': '1.0',
    'category': 'Accounting',
    'description': """
    Specific VAT Report for CY
    """,
    'author': '4Sight Group',
    'website': 'https://www.odoo.com/page/accounting',
    'depends': [
        'account',
        'account_reports',
    ],
    'data': [
        'data/paper_format_vat_cy.xml',
        'report/vat_report_template.xml',
    ],

    'assets': {
        'web.assets_backend': [
            # 'vat_report_cy/static/src/js/vat_report.js',
        ],
    },
}
