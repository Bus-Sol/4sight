# -*- coding: utf-8 -*-
{
    'name': '4Sight - Viva Wallet Payment Acquirer',
    'version': '1.0',
    'category': 'Accounting/Payment Acquirers',
    'summary': 'Payment Acquirer: Viva Wallet Implementation',
    'description': """
    Viva Wallet Implementation""",
    'author': '4Sight Group',
    'website': '',
    'depends': ['payment'],
    'data': [
        'views/payment_views.xml',
        'views/payment_viva_templates.xml',
        'data/payment_acquirer_data.xml',
        'views/journal_dashboard_kanban.xml'
    ],
    'demo': [
    ],
    'installable': True,
    'application': True,
}
