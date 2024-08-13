# -*- coding: utf-8 -*-
{
    'name': '4Sight Group - Viva Wallet',
    'category': 'Accounting/Payment Acquirers',
    'version': '17.0',
    'summary': '',
    "author": "4Sight Group",
    'description': """4Sight Group - Viva Wallet""",
    'depends': ['base', 'web', 'sale', 'purchase', 'account', 'payment'],
    'data': [
        'views/payment_viva_templates.xml',
        'views/payment_views.xml',
        'data/payment_acquirer_data.xml',
    ],
    'application': True,
    'installable': True,
    'uninstall_hook': 'uninstall_hook',
    'license': 'LGPL-3',
}
