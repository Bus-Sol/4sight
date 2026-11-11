from odoo import api, fields, models


class SaleOrderTemplate(models.Model):
    _inherit = 'sale.order.template'

    send_by_email_template_id = fields.Many2one(
        'mail.template', string='Send by Email Template',
        domain=[('model', '=', 'sale.order')],
    )
    is_flow_template = fields.Boolean(string="Flow Template")
    flow_image = fields.Binary(string="Flow Logo")
    flow_details = fields.Text(string="Flow Company Details")
    flow_email = fields.Char(string="Flow Email")
    flow_website = fields.Char(string="Flow Website")
    flow_phone = fields.Char(string="Flow Phone")
    flow_vat = fields.Char(string="Flow VAT")

