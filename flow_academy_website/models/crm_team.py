from odoo import fields, models


class CrmTeam(models.Model):
    _inherit = "crm.team"

    sale_order_template_id = fields.Many2one(
        "sale.order.template",
        string="Quotation Template",
    )
