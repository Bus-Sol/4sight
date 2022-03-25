# coding: utf-8
import logging
from odoo import api, fields, models, _
import datetime
_logger = logging.getLogger(__name__)


class SaleSub(models.Model):
    _inherit = 'sale.subscription'

    def trigger_cron_sub(self):
        res = True
        if self.recurring_next_date <= datetime.date.today() and self.template_id.payment_mode != 'manual':
            res = self._recurring_create_invoice(automatic=True)
        return res