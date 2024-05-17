# -*- coding: utf-8 -*-
{
    'name': 'Odoo Timestead',
    'category': '',
    'version': '17.0',
    'summary': '',
    'description': """  """,
    'author': '4Sight Group',
    'depends': [
        'contacts', 'product', 'sale_timesheet', 'account', 'portal', 'timer', 'analytic', 'project',
        'helpdesk', 'account_reports'
    ],
    'data': [
        'security/jobsheet_security.xml',
        'security/ir.model.access.csv',
        'data/jobsheet_project_data.xml',
        'data/data_jobsheet_seq.xml',
        'views/assets.xml',
        'views/designation_view.xml',
        'views/jobsheet_types_view.xml',
        'views/jobsheet_view.xml',
        'views/menu_jobsheet.xml',
        'views/view_account_move.xml',
        'wizard/batched_jobsheet.xml',
        'views/jobsheet_portal_template.xml',
        'views/view_partner_form.xml',
        'report/jobsheet_report_template.xml',
        'report/jobsheet_report.xml',
        'data/mail_template_data.xml',
        'views/res_config_settings_view.xml',
        'report/report_invoice_jobsheet.xml',
        'views/view_helpdesk_ticket.xml',
        'views/view_project_task.xml',
        'views/view_jobsheet_report.xml',
    ],
    'demo': [],
    'qweb': [
        # 'static/src/xml/digital_sign.xml',
    ],
    "assets": {
        "web.assets_backend": [
            # "odoo_timestead/static/src/js/digital_sign.js",
            # "odoo_timestead/static/src/css/jobsheet_customize_tickbox.css"
        ]
    },
    'installable': True,
    'application': True,
}
