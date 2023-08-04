# -*- coding: utf-8 -*-

{
    'name': 'Process Payment from Invoices',
    'version': '16.0.1.0.0',
    'category': 'Accounting',
    'description': """
    Register multiple payment from invoices with specific amount for each one 
    """,
    'author': '4Sight Group',
    'website': 'https://4sight.mt/',
    'depends': [
        'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/view_account_move_form.xml',
        'views/view_account_payment_register_form.xml',
    ],
    'qweb': [
        ],
    'demo' : [
    ],
}
