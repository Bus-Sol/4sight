from odoo import fields, models


class ReportProjectTaskUser(models.Model):
    _inherit = "report.project.task.user"

    invoice_id = fields.Many2one(comodel_name="account.move", string="Invoice")
    invoice_line_id = fields.Many2one(comodel_name="account.move.line", string="Invoice Line")

    invoice_total = fields.Float(string="Invoice Total Amount",group_operator="max", readonly=True)
    invoice_due = fields.Float(string="Invoice Due Amount", group_operator="max", readonly=True)

    real_progress = fields.Float(string="Task Progress", group_operator="avg", readonly=True)

    def _select(self):
        return super()._select() + (""",CASE WHEN COALESCE(t.allocated_hours, 0) = 0 THEN 0.0 ELSE (t.effective_hours * 100) / t.allocated_hours END as real_progress,
                                        aml.id as invoice_line_id, 
                                        am.id as invoice_id, 
                                        am.amount_total as invoice_total, 
                                        am.amount_residual as invoice_due
                                        """)

    def _group_by(self):
        return super()._group_by() + ",aml.id,am.id, am.amount_total, am.amount_residual"

    def _from(self):
        return super()._from() + """
            LEFT JOIN sale_order_line_invoice_rel soli_rel ON soli_rel.order_line_id = sol.id
            LEFT JOIN account_move_line aml ON aml.id = soli_rel.invoice_line_id
            LEFT JOIN account_move am ON am.id = aml.move_id
        """
