from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    sale_order_id = fields.Many2one(comodel_name="sale.order", string="Sale Order",
                                    compute="compute_sale_order", store=True)
    sale_order_template_id = fields.Many2one(comodel_name="sale.order.template", string="Sale Template",
                                             related="sale_order_id.sale_order_template_id", store=True)

    @api.depends('invoice_origin')
    def compute_sale_order(self):
        for rec in self:
            sale = self.env['sale.order'].search([('name','=',rec.invoice_origin)])
            if sale:
                rec.sale_order_id = sale.id
            else:
                rec.sale_order_id = False
