# -*- coding: utf-8 -*-
{
    'name': 'Open ticket from Log in',
    'category': 'Helpdesk',
    'version': '1.0',
    'summary': '',
    'description':
        """
        """,
    'author': '4Sight Group',
    'depends': ['base','website_helpdesk'],
    'data': [
        'data/connect_to_portal.xml',
        'views/helpdesk_form_view.xml',
        'views/website_template.xml',
        'views/helpdesk_template.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            '4sight/helpdesk_connect/static/src/js/submit_button.js',
        ],
    },
    'qweb': [
    ],
    'installable': True,
    'application': True,
}
