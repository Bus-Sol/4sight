# -*- coding: utf-8 -*-
from odoo import fields, models, api, modules, _
import logging
_logger = logging.getLogger(__name__)

class CrmLead(models.Model):
    _inherit = "crm.lead"

    @api.model
    def create(self, vals):
        res = super(CrmLead, self).create(vals)
        _logger.info('Res : %s', res)
        _logger.info('Vals : %s', vals)
        if 'company_id' in vals and vals.get('company_id') == False:
            res.company_id = 1
        return res