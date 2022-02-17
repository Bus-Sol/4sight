# -*- coding: utf-8 -*-

{
    'name': 'VAT Report MT',
    'version': '1.0',
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
        'views/assets.xml',
        'views/account_vat_report.xml',
        #'views/res_config_settings_view.xml',
    ],
    'qweb': [
        'static/src/xml/base.xml',
        ],
    'demo' : [
    ],
}
