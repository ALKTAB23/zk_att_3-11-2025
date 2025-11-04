# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Hemfa Custom HR Shifts',
    'version': '16.0.1.5',
    'category': 'Productivity/Notes',
    'description': """
This module update Shifts module
=================================================================
Update lists:
Version 1.0:
-- Extend hr attendance and add new fields related to shifts.
-- Attendance Sheet:
---- Extend hr attendance sheet to include shifts data before and after take decision about records that contain miss information and reflects status of employee in vacation, absent, public holiday
---- Link attendance sheet with payroll to deduct approved sheet after take decision of deduct for specific employee or batch of employees.
-- Add new shift records master data
-- Add feature to shift request (change) type
-- Apply and generate Work schedule for employees, department or tag
-- Add report of accumlate payroll report with specify of salary rules.
Version 1.1:
-- Extend holidays and read from shift data rather standard resource calendar 

""",
    'summary': '628_Hemfa_Custom_HR_Shifts - integrating Biometric Device With HR Attendance +integrating with payroll+ integrated whith time of + integrated work secheduel + payroll report',
    'depends': [
        'hr',
        'hr_attendance',
        'hr_holidays',
        'hr_employee_shift',
        'hr_attendance_sheet',
        'resource',
        'hr_payroll_community',
        'base',
        'hr_holidays',
        'oh_hr_zk_attendance'
    ],
    'data': [ 
        'security/ir.model.access.csv',
        'views/resource_calendar_custom_views.xml',
        'views/hr_attendance_policy_custom_views.xml',
        'views/hr_employee_contract_custom_views.xml',
        'views/hr_shift_generate_custom_views.xml',
        'views/shift_requests_views.xml',
        'views/hr_attendance_sheet_custom_views.xml',
        'views/salary_rules_data.xml',
        'views/hr_leave_type_view.xml',
        'wizard/report_payroll_wizard_views.xml',
        'report/report.xml',
        'report/accumlate_payrol_report.xml',
        'views/menus.xml',
        
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
