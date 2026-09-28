# -*- coding: utf-8 -*-
{
    'name': "MODIFY TIMESHEET ENTRIES",
    'author': "Fazal Ur Rahman",
    'category': 'Extra Tools',
    'version': '1.0',

    'depends': ['base', 'timesheet_grid', 'sale', 'purchase', 'product', 'account', 'odoo_timestead'],

    'data': [
        'views/views.xml',
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
