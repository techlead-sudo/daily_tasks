{
    'name': 'Daily Tasks',
    'version': '17.0.1.0.0',
    'summary': 'Employee Daily Task Management',
    'description': '''
        Daily Tasks Module
        ==================
        
        This module allows employees to record their daily tasks and provides
        HR/Managers with comprehensive reporting capabilities.
        
        Features:
        - Employee task recording with POD (Plan of the Day) and SOD (Summary of the Day)
        - Department and manager tracking
        - Access control based on user roles
        - Comprehensive reporting with graph and pivot views
        - Dashboard for task analytics
    ''',
    'author': 'Custom Development',
    'category': 'Human Resources',
    'depends': ['base', 'hr', 'mail'],
    'data': [
        'security/security.xml',
        'security/groups.xml',
        'security/ir.model.access.csv',
        'data/cron_data.xml',
        'views/daily_task_views.xml',
        'views/menuitems.xml',
    ],
    'demo': [
        'demo/daily_task_demo.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}