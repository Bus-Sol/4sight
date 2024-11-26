from odoo import api, fields, models


class Project(models.Model):
    _inherit = 'project.project'

    invoice_ids = fields.Many2many(comodel_name="account.move", string="Invoices", compute="get_invoices")
    invoice_total = fields.Float(string="Invoices Total Amount",group_operator="sum", compute="get_invoices")
    invoice_due = fields.Float(string="Invoices Due Amount", group_operator="sum", compute="get_invoices")
    tasks_allocated_hours = fields.Float(string="Allocated Hours", group_operator="sum", compute="get_project_hours")
    tasks_remaining_hours = fields.Float(string="Remaining Hours", group_operator="sum", compute="get_project_hours")
    effective_hours = fields.Float(string="Spent Hours", group_operator="sum", compute="get_project_hours")
    progress = fields.Float(string="Progress", group_operator="avg", compute="get_progress")

    paid_hours = fields.Float(string="Client Paid Hours")
    remaining_from_paid = fields.Float(string="Remaining hours from Client Paid",compute="get_project_hours")
    paid_progress = fields.Float(string="Paid Progress", group_operator="avg", compute="get_progress")

    achievements = fields.Text(string="Achievements", tracking=True)
    next_deliverables = fields.Text(string="Next Deliverables", tracking=True)
    dependencies = fields.Text(string="Issues/Risks/Dependencies", tracking=True)
    action_items = fields.Text(string="Action Items", tracking=True)

    def action_open_project(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('project.open_view_project_all')
        action["views"] = [
            (self.env.ref("project.edit_project").id, "form")
        ]
        action['res_id'] = self.id
        return action

    @api.depends('sale_order_id','sale_order_id.invoice_ids')
    def get_invoices(self):
        for rec in self:
            rec.invoice_ids = [(6, 0, [i.id for i in rec.sale_order_id.invoice_ids])]
            rec.invoice_total = sum([i.amount_total for i in rec.sale_order_id.invoice_ids])
            rec.invoice_due = sum([i.amount_residual for i in rec.sale_order_id.invoice_ids])

    @api.depends('task_ids.effective_hours','paid_hours')
    def get_project_hours(self):
        for rec in self:
            rec.effective_hours = sum([t.effective_hours for t in rec.task_ids])
            rec.tasks_allocated_hours = sum([t.allocated_hours for t in rec.task_ids])
            rec.tasks_remaining_hours = sum([t.allocated_hours - t.effective_hours for t in rec.task_ids])
            rec.remaining_from_paid = rec.paid_hours - rec.effective_hours


    @api.depends('effective_hours', 'tasks_allocated_hours','paid_hours')
    def get_progress(self):
        for rec in self:
            rec.progress = (rec.effective_hours * 100 ) / rec.tasks_allocated_hours if rec.tasks_allocated_hours > 0 else 0
            rec.paid_progress = (rec.effective_hours * 100 ) / rec.paid_hours if rec.paid_hours > 0 else 0

