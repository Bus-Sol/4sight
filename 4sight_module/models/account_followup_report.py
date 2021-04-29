# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.translate import _


class AccountFollowupReport(models.AbstractModel):
    _inherit = "account.followup.report"

    def _get_report_name(self):
        """
        Override
        Return the name of the report
        """
        return _('Statement Report')

    def get_report_filename(self, options):
        """The name that will be used for the file when downloading pdf,xlsx,..."""
        return self._get_report_name().lower().replace(' ', '_')