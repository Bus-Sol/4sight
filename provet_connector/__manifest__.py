{
    'name': 'Provet Cloud Connector',
    'version': '1.0.0',
    'category': 'Tools',
    'summary': 'Connect Odoo with Provet Cloud via OAuth2 API',
    'description': """
        Module to connect Odoo with Provet Cloud using OAuth2 authentication.
        Supports token management, automatic refresh, and API integration.
    """,
    'author': 'Mohamed Daoud',
    'depends': ['base','web'],
    'license': 'OPL-1 (Odoo Proprietary License v1.0)',
    'data': [
        'security/ir.model.access.csv',
        'views/provet_config_views.xml',
        # 'views/templates.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}