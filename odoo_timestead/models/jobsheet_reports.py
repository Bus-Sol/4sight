# -*- coding: utf-8 -*-

from odoo import models, api, _, _lt, fields
from odoo.tools.misc import format_date
from datetime import timedelta
from odoo.tools.misc import formatLang

from collections import defaultdict


class ReportJobsheetBalance(models.AbstractModel):
    # _inherit = "account.report"
    _inherit = 'account.report.custom.handler'
    _name = "jobsheet.balance.report.handler"
    _description = "Out of Balance Report"


    def _dynamic_lines_generator(self, report, options, all_column_groups_expression_totals,warnings=None):
        lines = []
        context = self.env.context
        # report = self.env['account.report']
        report_value = dict()
        prepaid_partners_with_services = self.env['res.partner'].search(
            [('jobsheet_type', '=', 'prepaid'), ('service_ids', '!=', False)], order='name')
        for partner in prepaid_partners_with_services:
            planned = 0
            effective = 0
            remaining = 0
            tks = False
            for service in partner.service_ids:                
                tks1 = self.env['project.task'].search(
                    [('partner_id', '=', partner.id), 
                     ('related_service_id', '=', service.product_id.id),
                     ('sale_line_id','!=',False),
                     ('sale_line_id.order_id.state','in',['sale','done'])],
                    order='id desc')
                tks = [task for task in tks1 if round(task.remaining_hours, 2) > 0]
                
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
                report_value[('%s_%s') % (partner.id, service.product_id.id)] = [
                    partner.name, service.product_id.name, '00:00', '00:00', '00:00', 'Out of Balance']

        prepaid_partners_without_services = self.env['res.partner'].search([
            ('jobsheet_type', '=', 'prepaid'),
            ('service_ids', '=', False)
        ], order='name')

        for partner in prepaid_partners_without_services:
            report_value[('%s') % partner.id] = [partner.name, 'No services', '00:00', '00:00', '00:00', 'Not Defined']

        columns = {}
        for key, val in report_value.items():
            columns[key] = [
                {'Service': val[1]},
                {'Planned Hours': val[2]},
                {'Hours Consumed': val[3]},
                {'Remaining Hours': val[4]},
                {'Status': val[5]},
            ]
        lines = []
        for partner_product in columns:
            column_values = []
            list_p_p = partner_product.split('_')
            partner_id = self.env['res.partner'].browse(int(list_p_p[0]))
            name = partner_id.name
            if len(list_p_p) > 1:
                product_id = self.env['product.template'].browse(int(list_p_p[1]))
                name = partner_id.name + " - " + product_id.name
            list_col = columns[partner_product]
            for column in options['columns']:
                for col in list_col:
                    if column.get('name') in col:
                        column_values.append({
                            'name': col.get(column.get('name')),
                            'no_format': col.get(column.get('name')),
                            'class': 'number'
                        })
            line_id = report._get_generic_line_id('res.partner', partner_id.id) if partner_id else report._get_generic_line_id('res.partner', None, markup='no_partner')

            lines.append((0, {
                # 'id': report._get_generic_line_id('res.partner', partner_id.id, markup=''),
                'id': report._get_generic_line_id('res.partner', partner_id.id),
                'name': _(name),
                'level': 1,
                'columns': column_values,
            }))
        return lines

    @api.model
    def _get_report_name(self):
        return _('Out of Balance Report')
