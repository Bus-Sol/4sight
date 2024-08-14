# -*- coding: utf-8 -*-


{
    'name': 'Sale Proposals',
    'version': '17.0',
    'summary': 'Sale Proposals',
    'category': 'Reporting',
    'author': 'Abrus Digital',
    'company': 'Abrus Digital',
    'maintainer': 'Abrus Digital',
    'live_test_url': 'https://youtube.com/shorts/KHe8IEwjVwQ',
    'depends': ['sale_management','sale'],
    'website': 'https://www.abrus.digital',
    'price': 80,
    'currency': "USD",
    'data': [
        'security/ir.model.access.csv',
        'views/sale_proposal_view.xml',
        'views/sequence_view.xml',
        'report/sale_proposal_report.xml',
        'report/report.xml',
        'data/quotation.xml',
        'data/proposal_mail.xml',
    ],
    'qweb': ["static/src/xml/*.xml"],
    'images': ['static/description/banner.gif'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
