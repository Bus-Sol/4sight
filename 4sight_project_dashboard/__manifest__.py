# -*- coding: utf-8 -*-
{
    'name': '4Sight Project Dashboard',
    'version': '17.0',
    'category': '',
    'description': """
        4Sight Project Dashboard
    """,
    'author': '4Sight Group| Mohamed Daoud',
    'website': '',
    'depends': [
        'project',
        'web',
        'board',
        'sale_project',
        'hr_timesheet',
        'sale_timesheet'
    ],
    'data': [
        'views/project_dashboard.xml',
        'views/taks_analysis_list.xml',
    ],
    'assets': {
        'web.assets_backend': [
            '4sight_project_dashboard/static/src/components/**/*.js',
            '4sight_project_dashboard/static/src/components/**/*.xml',
            '4sight_project_dashboard/static/src/components/**/*.scss',
        ],
    },
}
