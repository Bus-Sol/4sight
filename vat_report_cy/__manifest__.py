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
        'report/vat_report_template.xml',
        'views/assets.xml',
    ],
    'qweb': [
        ],
    'demo' : [
    ],
}
