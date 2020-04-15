{
    'name': "ABAKUS Equipment Management",
    'version': '11.0.1.0',
    'license': 'AGPL-3',
    'depends': [
        'hr_maintenance',
        'project',
        'sale_management',
        'stock',
        'sale_subscription',
        'hr_analytic_timesheet_improvements',
    ],
    'author': "ABAKUS IT-SOLUTIONS",
    'website': "http://www.abakusitsolutions.eu",
    'category': 'Human Resources',
    'data': [
        'wizards/create_asset_from_sale_wizard_view.xml',

        'views/equipment_category_view.xml',
        'views/equipment_view.xml',
        'views/res_partner_view.xml',
        'views/project_task_view.xml',
        'views/sale_order_view.xml',
        'views/sale_subscription_view.xml',
        'views/maintenance_task_model_view.xml',
        'views/maintenance_level_view.xml',
        'views/maintenance_request_view.xml',
        'views/account_analytic_line_view.xml',
        'views/security_check_view.xml',
        'views/security_check_settings_view.xml',

        'data/ir_sequence.xml',
        'data/ir_cron.xml',

        'reports/maintenance_request_report.xml',
        'reports/layouts.xml',
        'reports/external_access_template.xml',
        'reports/backups_template.xml',
        'reports/access_rights_template.xml',
        'reports/gate_access_template.xml',
        'reports/servers_security_template.xml',
        'reports/network_security_template.xml',
        'reports/workstations_security_template.xml',
        'reports/todos_template.xml',
        'reports/complete_report_template.xml',
        'reports/reports.xml',

        'security/res_groups.xml',
        'security/ir.model.access.csv',
    ],
}
