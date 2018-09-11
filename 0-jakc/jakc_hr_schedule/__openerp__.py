{
    'name': 'Jakc Labs - Employee Shift Scheduling',
    'version': '1.0',
    'category': 'Generic Modules/Human Resources',
    'description': """


Employee Shift Scheduling
=========================

Easily create, manage, and track employee schedules.


    """,
    'author': "Jakc Labs",
    'website': 'http://www.jakc-labs.com',
    'depends': [
        'hr','hr_contract','mail'
    ],
    "external_dependencies": {
        'python': ['dateutil'],
    },
    'data': [
        'wizards/process_absence_view.xml',
        'wizards/report_absence_view.xml',
        'wizards/report_absence_summary_view.xml',
        'wizards/process_exception_view.xml',
        'wizards/report_fingerprint_view.xml',
        'views/jakc_hr_schedule_view.xml',
        'views/jakc_hr_employee_view.xml',
        'views/jakc_hr_absence_view.xml',
        'views/jakc_hr_absence_report.xml',
        'views/jakc_hr_fingerprint_report.xml',
        'views/jakc_resource_calendar_view.xml',
        'views/report_absencedetails.xml',
        'views/report_absencesummary.xml',
        'views/report_fingerprintdetails.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
    ],
    'test': [
    ],
    'installable': True,
}
