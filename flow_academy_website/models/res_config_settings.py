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
    flow_remote_odoo_username = fields.Char(
        string='Remote username',
        config_parameter='flow_academy.remote_odoo_username',
    )
    flow_remote_odoo_password = fields.Char(
        string='Remote password',
        config_parameter='flow_academy.remote_odoo_password',
    )
