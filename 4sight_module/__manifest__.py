# -*- coding: utf-8 -*-
{
    'name': '4Sight - Module',
    'version': '16.0.1.0.0',
    'category': '',
    'description': """
    """,
    'author': '4Sight Group',
    'website': '',
    'depends': [
        'sale',
        'account',
        'account_reports',
        'account_followup',
        'web',
        'report_qweb_element_page_visibility',
        'helpdesk',
        'crm',
        "mail"
    ],
    'data': [
        'views/account_followups.xml',
        'views/sale_view.xml',
        'report/external_layout_background.xml',
        'views/view_helpdesk_form.xml',
        'views/view_helpdesk_team.xml',
        'views/view_crm_kanban.xml',
        'views/view_account_inv_send.xml',
        'views/view_partner_form.xml',
    ],
    'demo': [
    ],
}
