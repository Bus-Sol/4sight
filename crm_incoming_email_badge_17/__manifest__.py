{
    "name": "CRM Incoming Email Badge",
    "version": "17.0.2.0.0",
    "category": "Sales/CRM",
    "summary": "Shows waiting and replied email status on CRM Kanban cards",
    "description": '''
CRM Incoming Email Badge
========================

Red badge:
    A customer email is waiting for an internal reply.

Green badge:
    An internal user has replied after the latest customer email.

The module does not add a CRM inbox, browser notifications, or a dashboard.
    ''',
    "author": "Lucija",
    "license": "LGPL-3",
    "depends": [
        "crm",
        "mail",
    ],
    "data": [
        "views/crm_lead_kanban_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "crm_incoming_email_badge_17/static/src/scss/crm_incoming_email_badge.scss",
        ],
    },
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
    "auto_install": False,
}
