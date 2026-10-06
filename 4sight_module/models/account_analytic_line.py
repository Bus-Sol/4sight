from odoo import api, fields, models
from odoo.exceptions import UserError


class AnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    def write(self, vals):
        """Enforce SLA and contracted-hours limits when a timesheet is updated."""
        result = super().write(vals)

        for record in self:
            task = record.task_id
            project = record.project_id

            if task and any(tag.x_track_date for tag in task.tag_ids):
                if not task.date_deadline:
                    raise UserError('You can not record timesheet before setting Deadline.')
                if task.date_deadline < fields.Datetime.now():
                    raise UserError('You can not record timesheet on expired SLA.')

            if task and any(tag.x_track_spent_hours for tag in task.tag_ids):
                if task.effective_hours > task.allocated_hours:
                    raise UserError('You can not exceed the allocated hours.')

            if not project or not any(tag.x_track_spent_hours for tag in project.tag_ids):
                continue

            if project.effective_hours > project.paid_hours:
                raise UserError('You can not exceed the paid hours.')

            if project.paid_hours * 0.7 < project.effective_hours and not project.x_passed:
                project.x_passed = True
                activity_type = self.env.ref('4sigth.project_hours_70')
                for user in project.company_id.x_project_notification_75:
                    project.activity_schedule(
                        date_deadline=fields.Date.today(),
                        activity_type_id=activity_type.id,
                        summary='Spent Hours Exceeded 70% of Paid.',
                        user_id=user.id,
                    )

            if project.paid_hours * 0.8 < project.effective_hours and not project.x_approve_pass:
                raise UserError('Please ask the project manager to approve passing 80% of the paid hours.')

        return result

