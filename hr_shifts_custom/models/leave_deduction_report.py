# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, date
import logging

_logger = logging.getLogger(__name__)


class LeaveDeductionReport(models.TransientModel):
    """تقرير خصومات الإجازة السنوية للموظف"""
    _name = 'leave.deduction.report'
    _description = 'Leave Deduction Report'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    date_from = fields.Date(string='From Date', required=True,
                            default=lambda self: fields.Date.to_string(date.today().replace(month=1, day=1)))
    date_to = fields.Date(string='To Date', required=True,
                          default=lambda self: fields.Date.today())
    
    # إحصائيات إجمالية
    total_leave_balance = fields.Float(string='Total Leave Balance (Days)', compute='_compute_deductions')
    total_deducted = fields.Float(string='Total Deducted (Days)', compute='_compute_deductions')
    remaining_balance = fields.Float(string='Remaining Balance (Days)', compute='_compute_deductions')
    
    # تفاصيل الخصومات
    deduction_line_ids = fields.One2many('leave.deduction.report.line', 'report_id', 
                                         string='Deduction Details', compute='_compute_deductions')

    @api.depends('employee_id', 'date_from', 'date_to')
    def _compute_deductions(self):
        for record in self:
            # 1. حساب رصيد الإجازة الكلي
            holiday_ids = self.env['hr.leave.type'].search([
                ('requires_allocation', '=', 'yes'),
                ('attendance_deduct', '=', True)
            ])
            
            leave_allocations = self.env['hr.leave.allocation'].search([
                ('employee_id', '=', record.employee_id.id),
                ('state', '=', 'validate'),
                ('holiday_status_id', 'in', holiday_ids.ids)
            ])
            
            total_allocations = sum(leave_allocations.mapped('number_of_days'))
            
            # 2. حساب الإجازات المأخوذة
            leaves = self.env['hr.leave'].search([
                ('employee_id', '=', record.employee_id.id),
                ('state', '=', 'validate'),
                ('holiday_status_id', 'in', holiday_ids.ids)
            ])
            total_leaves_taken = sum(leaves.mapped('number_of_days'))
            
            # 3. حساب الخصومات من Attendance Sheets
            deducted_allocations = self.env['hr.leave.allocation'].search([
                ('employee_id', '=', record.employee_id.id),
                ('att_sheet_id', '!=', False),
                ('att_sheet_id.date_from', '>=', record.date_from),
                ('att_sheet_id.date_to', '<=', record.date_to),
                ('state', '=', 'validate'),
                ('holiday_status_id', 'in', holiday_ids.ids)
            ])
            
            total_deducted = sum(deducted_allocations.mapped('att_sheet_deduct'))
            
            # 4. الرصيد المتبقي
            record.total_leave_balance = total_allocations
            record.total_deducted = total_deducted
            record.remaining_balance = total_allocations - total_leaves_taken - total_deducted
            
            # 5. إنشاء سطور تفصيلية للخصومات (استخدام command format للـ Transient Model)
            line_vals = []
            for allocation in deducted_allocations:
                att_sheet = allocation.att_sheet_id
                
                # حساب تفاصيل الخصم من الـ Attendance Sheet
                late_hours = att_sheet.late_policy_hours
                diff_hours = att_sheet.diff_policy_hours
                absence_hours = att_sheet.tot_absence
                forget_hours = att_sheet.forget_hours
                
                # حساب عدد الساعات في اليوم
                hours_per_day = att_sheet.employee_id.resource_calendar_id.hours_per_day if att_sheet.employee_id.resource_calendar_id else 8.0
                
                # إضافة إلى القائمة
                line_vals.append((0, 0, {
                    'att_sheet_id': att_sheet.id,
                    'sheet_name': att_sheet.name,
                    'date_from': att_sheet.date_from,
                    'date_to': att_sheet.date_to,
                    'late_hours': late_hours,
                    'diff_hours': diff_hours,
                    'absence_hours': absence_hours,
                    'forget_hours': forget_hours,
                    'total_hours': late_hours + diff_hours + absence_hours + forget_hours,
                    'deducted_days': allocation.att_sheet_deduct,
                    'hours_per_day': hours_per_day,
                    'leave_type_id': allocation.holiday_status_id.id,
                }))
            
            # تعيين السطور باستخدام command format
            record.deduction_line_ids = line_vals

    def action_print_report(self):
        """طباعة التقرير"""
        return self.env.ref('hr_shifts_custom.action_report_leave_deduction').report_action(self)

    def action_view_report(self):
        """عرض التقرير في الشاشة"""
        self.ensure_one()
        return {
            'name': _('Leave Deduction Report'),
            'type': 'ir.actions.act_window',
            'res_model': 'leave.deduction.report',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }


class LeaveDeductionReportLine(models.TransientModel):
    """سطر تفصيلي لخصومات الإجازة"""
    _name = 'leave.deduction.report.line'
    _description = 'Leave Deduction Report Line'
    _order = 'date_from desc'

    report_id = fields.Many2one('leave.deduction.report', string='Report', required=True, ondelete='cascade')
    att_sheet_id = fields.Many2one('attendance.sheet', string='Attendance Sheet')
    sheet_name = fields.Char(string='Sheet Name')
    date_from = fields.Date(string='From')
    date_to = fields.Date(string='To')
    
    # تفاصيل الساعات
    late_hours = fields.Float(string='Late Hours')
    diff_hours = fields.Float(string='Diff Time Hours')
    absence_hours = fields.Float(string='Absence Hours')
    forget_hours = fields.Float(string='Forget Hours')
    total_hours = fields.Float(string='Total Hours')
    
    # الخصم
    hours_per_day = fields.Float(string='Hours/Day')
    deducted_days = fields.Float(string='Deducted Days')
    leave_type_id = fields.Many2one('hr.leave.type', string='Leave Type')
