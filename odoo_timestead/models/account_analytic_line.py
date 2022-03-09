# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    job_id = fields.Many2one('client.jobsheet', 'Jobsheet', index=True)
    unit_amount = fields.Float('Hours')

    def unlink(self):
        for rec in self:
            if rec.job_id and not self.env.user.has_group('odoo_timestead.group_jobsheet_manager'):
                raise UserError(_('You cannot delete this timesheet, please contact your Administrator.'))
        return super(AccountAnalyticLine, self).unlink()