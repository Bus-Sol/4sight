# -*- coding: utf-8 -*-
{
    'name': '4Sight Group -  Viva Wallet',
    'category': 'Accounting/Payment Acquirers',
    'version': '1.0',
    'summary': '',
    "author": "4Sight Group",
    'description':
        """
        """,
    'depends': ['payment', 'account'],
    'data': [
        'views/payment_viva_templates.xml',
        'views/payment_views.xml',
        'data/payment_acquirer_data.xml',

    ],
    'application': True,
    'uninstall_hook': 'uninstall_hook',
    'license': 'LGPL-3',
}
