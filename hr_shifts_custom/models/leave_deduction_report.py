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
    
    # تفاصيل الخصومات (كـ Many2many بدون cascade لتجنب مشاكل TransientModel)
    deduction_line_ids = fields.Many2many('attendance.sheet', 
                                          string='Attendance Sheets',
                                          compute='_compute_deductions')

    @api.depends('employee_id', 'date_from', 'date_to')
    def _compute_deductions(self):
        for record in self:
            # تهيئة القيم الافتراضية
            record.total_leave_balance = 0.0
            record.total_deducted = 0.0
            record.remaining_balance = 0.0
            record.deduction_line_ids = [(5, 0, 0)]  # Clear all
            
            if not record.employee_id or not record.date_from or not record.date_to:
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
            
            # 3. البحث عن Attendance Sheets التي تم فيها خصم من الإجازة
            att_sheets = self.env['attendance.sheet'].search([
                ('employee_id', '=', record.employee_id.id),
                ('date_from', '>=', record.date_from),
                ('date_to', '<=', record.date_to),
                ('state', 'in', ['done', 'confirm']),
                ('sheet_action', '=', 'deduct_leave')  # فقط التي تم خصمها من الإجازة
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
            
            # 6. تعيين attendance sheets مباشرة باستخدام command format
            record.deduction_line_ids = [(6, 0, att_sheets.ids)]

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



