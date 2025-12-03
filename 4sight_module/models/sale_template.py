from odoo import api, fields, models


class SaleOrderTemplate(models.Model):
    _inherit = 'sale.order.template'

    is_flow_template = fields.Boolean(string="Flow Template")
    flow_image = fields.Binary(string="Flow Logo")
    flow_details = fields.Text(string="Flow Company Details")
    flow_email = fields.Char(string="Flow Email")
    flow_website = fields.Char(string="Flow Website")
    flow_phone = fields.Char(string="Flow Phone")
    flow_vat = fields.Char(string="Flow VAT")

