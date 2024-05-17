# -*- coding: utf-8 -*-

{
    'name': 'VAT Report MT',
    'version': '17.0',
    'category': 'Accounting',
    'description': """
    Specific VAT Report for MT
    """,
    'author': '4Sight Group',
    'website': 'https://www.odoo.com/page/accounting',
    'depends': [
        'account',
        'account_reports',
    ],
    'data': [
        'report/vat_report_template.xml',
        # 'views/assets.xml',
        'views/account_vat_report.xml',
    ],
    'assets': {
        'web.assets_backend': [
            # '/vat_report_mt/static/src/js/vat_report.js'
        ]
    },
    'qweb': [
        # 'static/src/xml/base.xml',
        ],
    'demo' : [
    ],
}
