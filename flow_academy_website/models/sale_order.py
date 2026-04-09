from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _compute_sale_order_template_id(self):
        Lead = self.env["crm.lead"]
        for order in self:
            if "website_id" in self._fields and order.website_id:
                continue

            lead = order.opportunity_id
            if not lead and self.env.context.get("default_opportunity_id"):
                lead = Lead.browse(self.env.context["default_opportunity_id"])

            if lead:
                order.sale_order_template_id = lead.team_id.sale_order_template_id.id or False
                continue

            super(SaleOrder, order)._compute_sale_order_template_id()
