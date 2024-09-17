# -*- coding: utf-8 -*-
{
    'name': '4Sight Group - Revolut Payment',
    'category': 'Accounting/Payment Acquirers',
    'version': '17.0',
    'summary': '',
    "author": "4Sight Group| Mohamed Daoud",
    'description': """4Sight Group - Revolut Payment""",
    'depends': ['payment'],
    'data': [
        'views/payment_provider.xml',
        'views/payment_templates.xml',
        'data/payment_provider_data.xml',
    ],
    'application': True,
    'installable': True,
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'license': 'LGPL-3',
}
