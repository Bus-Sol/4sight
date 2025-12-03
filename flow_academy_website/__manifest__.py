# -*- coding: utf-8 -*-
{
    'name': 'Flow Academy ',
    'version': '17.0',
    'category': '',
    'description': """
        Flow Academy
    """,
    'author': '4Sight Group| Mohamed Daoud',
    'website': '',
    'depends': [
        'base',
        'website',
        'web',
        'event',
        'website_event',
        'website_sale',
        'account',
        'website_event_sale'
    ],
    'data': [
        'views/event_category.xml',
        'views/event.xml',
        'views/website_templates.xml',
        'security/ir.model.access.csv'
    ],

}
