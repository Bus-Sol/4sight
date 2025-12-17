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
        'views/ticket_registration.xml',
        'views/address_template.xml',
        'security/ir.model.access.csv'
    ],
    'assets': {
        'web.assets_frontend': [
            'flow_academy_website/static/src/js/website_sale.js',
            'flow_academy_website/static/src/scss/styles.scss',
        ],
    },

}
