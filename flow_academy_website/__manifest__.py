# -*- coding: utf-8 -*-
{
    'name': 'Flow Academy ',
    'version': '17.0',
    'category': 'Web Events',
    'description': """
        Flow Academy
    """,
    'author': '4Sight Group| Mohamed Daoud',
    'website': '',
    'license': 'OPL-1',
    'depends': [
        'base',
        'website',
        'web',
        'crm',
        'sale_crm',
        'sale_management',
        'event',
        'event_sale',
        'website_event',
        'website_sale',
        'account',
        'website_event_sale'
    ],
    'data': [
        'views/crm_lead.xml',
        'views/crm_team.xml',
        'views/event_category.xml',
        'views/event.xml',
        'views/event_question.xml',
        'views/event_registration_answer.xml',
        'views/website_templates.xml',
        'views/ticket_registration.xml',
        'views/address_template.xml',
        'views/email_templates.xml',
        'views/event_templates.xml',

        'security/ir.model.access.csv'
    ],
    'assets': {
        'web.assets_frontend': [
            'flow_academy_website/static/src/js/website_sale.js',
            'flow_academy_website/static/src/scss/styles.scss',
        ],
    },

}
