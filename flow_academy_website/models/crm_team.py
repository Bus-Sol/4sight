from odoo import fields, models


class CrmTeam(models.Model):
    _inherit = "crm.team"

    sale_order_template_id = fields.Many2one(
        "sale.order.template",
        string="Quotation Template",
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        check_company=True,
    )
