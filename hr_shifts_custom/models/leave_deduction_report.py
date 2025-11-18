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
    total_leave_balance = fields.Float(string='Total Leave Balance (Days)', compute='_compute_deductions', store=False)
    total_deducted = fields.Float(string='Total Deducted (Days)', compute='_compute_deductions', store=False)
    remaining_balance = fields.Float(string='Remaining Balance (Days)', compute='_compute_deductions', store=False)
    
    # تفاصيل الخصومات
    deduction_line_ids = fields.One2many('leave.deduction.report.line', 'report_id', 
                                         string='Deduction Details')

    @api.onchange('employee_id', 'date_from', 'date_to')
    def _onchange_filters(self):
        """Update report data when filters change"""
        self._compute_deductions()
    
    @api.depends('employee_id', 'date_from', 'date_to')
    def _compute_deductions(self):
        for record in self:
            if not record.employee_id or not record.date_from or not record.date_to:
                record.total_leave_balance = 0.0
                record.total_deducted = 0.0
                record.remaining_balance = 0.0
                continue
            
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
            
            # 3. البحث عن كل Attendance Sheets في الفترة المحددة
            att_sheets = self.env['attendance.sheet'].search([
                ('employee_id', '=', record.employee_id.id),
                ('date_from', '>=', record.date_from),
                ('date_to', '<=', record.date_to),
                ('state', 'in', ['done', 'confirm'])
            ], order='date_from desc')
            
            _logger.info(f"📊 عدد Attendance Sheets للموظف {record.employee_id.name}: {len(att_sheets)}")
            
            # 4. حساب إجمالي الخصومات
            total_deducted = 0.0
            for sheet in att_sheets:
                # البحث عن allocation مرتبط بهذا الـ sheet
                allocation = self.env['hr.leave.allocation'].search([
                    ('employee_id', '=', record.employee_id.id),
                    ('att_sheet_id', '=', sheet.id),
                    ('state', '=', 'validate'),
                ], limit=1)
                
                if allocation:
                    total_deducted += allocation.att_sheet_deduct
            
            # 5. الرصيد المتبقي
            record.total_leave_balance = total_allocations
            record.total_deducted = total_deducted
            record.remaining_balance = total_allocations - total_leaves_taken - total_deducted
            
            # 6. حذف السطور القديمة
            record.deduction_line_ids.unlink()
            
            # 7. إنشاء سطور جديدة لكل Attendance Sheet
            for att_sheet in att_sheets:
                # حساب تفاصيل الخصم من الـ Attendance Sheet
                late_hours = att_sheet.late_policy_hours or 0.0
                diff_hours = att_sheet.diff_policy_hours or 0.0
                absence_hours = att_sheet.tot_absence or 0.0
                forget_hours = att_sheet.forget_hours or 0.0
                
                # حساب عدد الساعات في اليوم
                hours_per_day = att_sheet.employee_id.resource_calendar_id.hours_per_day if att_sheet.employee_id.resource_calendar_id else 8.0
                
                # البحث عن allocation مرتبط
                allocation = self.env['hr.leave.allocation'].search([
                    ('employee_id', '=', record.employee_id.id),
                    ('att_sheet_id', '=', att_sheet.id),
                    ('state', '=', 'validate'),
                ], limit=1)
                
                deducted_days = allocation.att_sheet_deduct if allocation else 0.0
                leave_type_id = allocation.holiday_status_id.id if allocation else False
                
                _logger.info(f"  📅 Sheet: {att_sheet.name}, Late: {late_hours}h, Diff: {diff_hours}h, Absence: {absence_hours}h, Forget: {forget_hours}h, Deducted: {deducted_days} days")
                
                # إنشاء السطر
                self.env['leave.deduction.report.line'].create({
                    'report_id': record.id,
                    'att_sheet_id': att_sheet.id,
                    'sheet_name': att_sheet.name,
                    'date_from': att_sheet.date_from,
                    'date_to': att_sheet.date_to,
                    'late_hours': late_hours,
                    'diff_hours': diff_hours,
                    'absence_hours': absence_hours,
                    'forget_hours': forget_hours,
                    'total_hours': late_hours + diff_hours + absence_hours + forget_hours,
                    'deducted_days': deducted_days,
                    'hours_per_day': hours_per_day,
                    'leave_type_id': leave_type_id,
                })

    def action_print_report(self):
        """طباعة التقرير"""
        self.ensure_one()
        # تحديث البيانات قبل الطباعة
        self._compute_deductions()
        # طباعة التقرير
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
