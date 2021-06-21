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
    'depends': ['base','mail','web','website_helpdesk_form'],
    'data': [
        'data/connect_to_portal.xml',
        'views/assets.xml',
        'views/helpdesk_form_view.xml',
        'views/website_template.xml',
        'views/helpdesk_template.xml',
    ],
    'demo': [
    ],
    'qweb': [
    ],
    'installable': True,
    'application': True,
}
