{
    'name': 'Project Profitability Report',
    'version': '17.0.1.0.0',
    'category': 'Accounting/Reporting',
    'summary': 'Sales order and project profitability report for accounting',
    'description': '''
Project Profitability Report for Odoo 17
========================================
Provides an accounting-oriented profitability report by project and sales order,
including confirmed sales, invoiced revenue, purchase commitments, vendor bills,
timesheet cost, expenses, total cost, margin and margin percentage.
''',
    'author': 'Lucija',
    'license': 'LGPL-3',
    'depends': [
        'account',
        'analytic',
        'sale_management',
        'sale_project',
        'project',
        'hr_timesheet',
        'purchase',
        'hr_expense',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/project_profitability_report_views.xml',
    ],
    'installable': True,
    'application': False,
}
