# -*- coding: utf-8 -*-
from odoo import models


SKIP_JOBSHEET_SPLIT_ROUNDING_CONTEXT_KEY = "odoo_timestead_skip_split_rounding"


class BaseAutomation(models.Model):
    _inherit = "base.automation"

    def _is_timesheet_quarter_hour_rounding(self):
        self.ensure_one()
        automation = self.sudo()
        return automation.model_name == "account.analytic.line" and any(
            action.state == "code"
            and "record['unit_amount']" in (action.code or "")
            and "number % 0.25" in (action.code or "")
            for action in automation.action_server_ids
        )

    def _process(self, records, domain_post=None):
        if (
            self.env.context.get(SKIP_JOBSHEET_SPLIT_ROUNDING_CONTEXT_KEY)
            and self._is_timesheet_quarter_hour_rounding()
        ):
            return None
        return super()._process(records, domain_post=domain_post)
