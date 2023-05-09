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

    def _dynamic_lines_generator(self, report, options, all_column_groups_expression_totals):
        lines = []
        context = self.env.context
        report = self.env['account.report']
        query = """
            SELECT
                DISTINCT ON (partner.name, product.name, task.check_balance)
                partner.name, product.name,
                CASE WHEN (task.check_balance = 'balanced') THEN 'Balanced'
                ELSE 'Unbalanced' END
                FROM project_task task 
                RIGHT JOIN res_partner partner ON partner.id = task.partner_id
                LEFT JOIN product_template product ON product.id = task.related_service_id
                WHERE partner.jobsheet_type = 'prepaid'
                ORDER BY task.check_balance, product.name, partner.name;
        """
        report_value = dict()
        prepaid_partners_with_services = self.env['res.partner'].search(
            [('jobsheet_type', '=', 'prepaid'), ('service_ids', '!=', False)], order='name')
        for partner in prepaid_partners_with_services:
            for service in partner.service_ids:
                task = self.env['project.task'].search([
                    ('partner_id', '=', partner.id),
                    ('related_service_id', '=', service.product_id.id)
                ], limit=1, order='id desc')
                if task:
                    planned_hours = '{0:02.0f}:{1:02.0f}'.format(*divmod(task.planned_hours * 60, 60))
                    effective_hours = '{0:02.0f}:{1:02.0f}'.format(*divmod(task.effective_hours * 60, 60))
                    remaining_hours = '{0:02.0f}:{1:02.0f}'.format(*divmod(task.remaining_hours * 60, 60))
                    report_value[('%s_%s') % (partner.id, service.product_id.id)] = [
                        partner.name, service.product_id.name, planned_hours, effective_hours,
                        remaining_hours, dict(task._fields['check_balance'].selection).get(task.check_balance)
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
            lines.append((0, {
                'id': report._get_generic_line_id(None, None, markup=''),
                'name': _(name),
                'level': 1,
                'columns': column_values,
            }))
        return lines

    @api.model
    def _get_report_name(self):
        return _('Out of Balance Report')
