# -*- coding: utf-8 -*-

from odoo import models, api, _, _lt, fields
from odoo.tools.misc import format_date
from datetime import timedelta
from odoo.tools.misc import formatLang

from collections import defaultdict


class ReportJobsheetBalance(models.AbstractModel):
    _inherit = "account.report"
    _name = "jobsheet.balance.report"
    _description = "Out of Balance Report"

    filter_date = {'mode': 'range', 'filter': 'this_year'}
    filter_all_entries = False
    filter_unfold_all = False
    filter_unreconciled = False
    filter_partner = True

    def _get_columns_name(self, options):
        columns = [
            {},
            {'name': _('Service')},
            {'name': _('Planned Hours')},
            {'name': _('Hours Consumed')},
            {'name': _('Remaining Hours')},
            {'name': _('Status')},
        ]

        return columns

    @api.model
    def _get_lines(self, options, line_id=None):
        lines = []
        context = self.env.context

        report_value = dict()
        prepaid_partners_with_services = self.env['res.partner'].search(
            [('jobsheet_type', '=', 'prepaid'), ('service_ids', '!=', False)], order='name')
        for partner in prepaid_partners_with_services:

            for service in partner.service_ids:                
                tks1 = self.env['project.task'].search(
                    [('partner_id', '=', partner.id), 
                     ('related_service_id', '=', service.product_id.id),
                     ('sale_line_id','!=',False),
                     ('sale_line_id.order_id.state','in',['sale','done'])],
                    order='id desc')


                tks = [task for task in tks1 if round(task.remaining_hours, 2) > 0]

                planned = 0
                effective = 0
                remaining = 0
                for tsk in tks:
                    planned += tsk.planned_hours
                    effective += tsk.effective_hours
                    remaining += tsk.remaining_hours

                if tks:
                    planned_hours = '{0:02.0f}:{1:02.0f}'.format(*divmod(planned * 60, 60))
                    effective_hours = '{0:02.0f}:{1:02.0f}'.format(*divmod(effective * 60, 60))
                    remaining_hours = '{0:02.0f}:{1:02.0f}'.format(*divmod(remaining * 60, 60))
                    report_value[('%s_%s') % (partner.id, service.product_id.id)] = [partner.name,
                                                                                     service.product_id.name,
                                                                                     planned_hours,
                                                                                     effective_hours,
                                                                                     remaining_hours,
                                                                                     "Balanced"
                                                                                     ]       
                                                                                     
                else:
                    report_value[('%s_%s') % (partner.id, service.product_id.id)] = [partner.name,
                                                                                     service.product_id.name, '00:00','00:00','00:00', 'Out of Balance']

        prepaid_partners_without_services = self.env['res.partner'].search(
            [('jobsheet_type', '=', 'prepaid'), ('service_ids', '=', False)], order='name')
        for partner in prepaid_partners_without_services:
            report_value[('%s') % partner.id] = [partner.name, 'No services', '00:00','00:00','00:00', 'Not Defined']

        print(report_value)

        groupby_balance = {}

        for key, val in report_value.items():
            columns = [
                {'name': val[1]},
                {'name': val[2]},
                {'name': val[3]},
                {'name': val[4]},
                {'name': val[5]},

            ]

            lines.append({
                'id': key.split('_')[0],
                'name': val[0],
                'columns': [v for v in columns],
                'unfoldable': False,
                'level': 2,
                'unfolded': False,
            })
        return lines

    @api.model
    def _get_report_name(self):
        return _('Out of Balance Report')
