from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    flow_remote_odoo_url = fields.Char(
        string='Remote Odoo URL',
        config_parameter='flow_academy.remote_odoo_url',
        help='Base URL of the Odoo instance that receives Flow Academy newsletter contacts.',
    )
    flow_remote_odoo_db = fields.Char(
        string='Remote database',
        config_parameter='flow_academy.remote_odoo_db',
    )
    flow_remote_odoo_api_key = fields.Char(
        string='Remote API key',
        config_parameter='flow_academy.remote_odoo_api_key',
        help='API key of the remote Odoo 19 user used for JSON-2 requests.',
    )
