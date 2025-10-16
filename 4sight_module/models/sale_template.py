from odoo import api, fields, models


class SaleOrderTemplate(models.Model):
    _inherit = 'sale.order.template'

    is_flow_template = fields.Boolean(string="Flow Template")
    flow_image = fields.Binary(string="Flow Logo")
    flow_details = fields.Text(string="Flow Company Details")
