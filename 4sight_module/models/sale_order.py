from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_quotation_send(self):
        return super(SaleOrder, self.with_context(
            use_quotation_email_template=True,
        )).action_quotation_send()

    def _find_mail_template(self):
        self.ensure_one()
        template = self.sale_order_template_id.send_by_email_template_id
        if (self.env.context.get('use_quotation_email_template')
                and not self.env.context.get('proforma') and template):
            return template
        return super()._find_mail_template()
