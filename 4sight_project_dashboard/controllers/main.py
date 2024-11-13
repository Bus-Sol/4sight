import datetime
from odoo import http
from odoo.http import request


class ProjectFilter(http.Controller):

    @http.route('/project/filter', auth='public', type='json')
    def project_filter(self):
        """Summary:
            transferring data to the selection field that works as a filter
        Returns:
            type:list of lists, it contains the data for the corresponding
            filter."""
        project_list = []
        employee_list = []
        project_ids = request.env['project.project'].search([])
        employee_ids = request.env['hr.employee'].search([])
        # getting partner data
        for employee_id in employee_ids:
            dic = {'name': employee_id.name,
                   'id': employee_id.id}
            employee_list.append(dic)
        for project_id in project_ids:
            dic = {'name': project_id.name,
                   'id': project_id.id}
            project_list.append(dic)
        print('projects', project_list)
        return [project_list, employee_list]