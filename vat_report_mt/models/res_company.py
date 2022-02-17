# -*- coding: utf-8 -*-
from odoo import models, fields, _, api
from odoo.tools import date_utils
import datetime
from dateutil.relativedelta import relativedelta



class ResCompany(models.Model):
    _inherit = "res.company"

    limit_tax_backdate = fields.Boolean('Limit tax backdates to one tax period')
    max_tax_amount = fields.Float('Maximum tax amount for historic period')

    def _get_previous_tax_period(self, date):
        """ Returns Previsous Tax Period
        based on Periodicity from Accounting/Settings
        """
        self.ensure_one()
        period_months = self._get_tax_periodicity_months_delay()
        period_number = (date.month//period_months) + (1 if date.month % period_months != 0 else 0) - 1
        end_date = date_utils.end_of(datetime.date(date.year, period_number * period_months, 1), 'month')
        start_date = end_date + relativedelta(day=1, months=-period_months + 1)

        return start_date, end_date

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'


    limit_tax_backdate = fields.Boolean(related='company_id.limit_tax_backdate', string='Limit tax backdates to one tax period', readonly=False)
    max_tax_amount = fields.Float(related='company_id.max_tax_amount', string='Maximum tax amount for historic period', readonly=False)