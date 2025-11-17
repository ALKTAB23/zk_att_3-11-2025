# -*- coding: utf-8 -*-

##############################################################################
#
#    Annual Leave Deduction Report
#    Shows deductions from annual leave due to late/absence/early checkout
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, date
from dateutil.relativedelta import relativedelta


class HrLeaveDeductionReport(models.TransientModel):
    _name = 'hr.leave.deduction.report'
    _description = 'Annual Leave Deduction Report'

    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Employee',
        required=True,
        default=lambda self: self.env.user.employee_id.id
    )
    date_from = fields.Date(
        string='Date From',
        required=True,
        default=lambda self: fields.Date.to_string(
            date.today().replace(month=1, day=1)
        ),
        help="Start date for calculating deductions"
    )
    date_to = fields.Date(
        string='Date To',
        required=True,
        default=lambda self: fields.Date.to_string(date.today()),
        help="End date for calculating deductions"
    )
    
    # Leave Balance
    annual_leave_days = fields.Float(
        string='Annual Leave Entitlement (Days)',
        compute='_compute_leave_balance',
        help="Total annual leave days allocated"
    )
    leave_taken_days = fields.Float(
        string='Leave Taken (Days)',
        compute='_compute_leave_balance',
        help="Days taken as actual leave requests"
    )
    
    # Deductions from Attendance Issues
    late_deduction_hours = fields.Float(
        string='Late In Deduction (Hours)',
        compute='_compute_deductions',
        help="Hours deducted due to late check-in"
    )
    late_deduction_days = fields.Float(
        string='Late In Deduction (Days)',
        compute='_compute_deductions',
        help="Days deducted due to late check-in (hours / 8)"
    )
    
    diff_deduction_hours = fields.Float(
        string='Early Checkout Deduction (Hours)',
        compute='_compute_deductions',
        help="Hours deducted due to early checkout"
    )
    diff_deduction_days = fields.Float(
        string='Early Checkout Deduction (Days)',
        compute='_compute_deductions',
        help="Days deducted due to early checkout (hours / 8)"
    )
    
    absence_deduction_hours = fields.Float(
        string='Absence Deduction (Hours)',
        compute='_compute_deductions',
        help="Hours deducted due to absence"
    )
    absence_deduction_days = fields.Float(
        string='Absence Deduction (Days)',
        compute='_compute_deductions',
        help="Days deducted due to absence (hours / 8)"
    )
    
    total_deduction_days = fields.Float(
        string='Total Deduction (Days)',
        compute='_compute_deductions',
        help="Total days deducted from annual leave"
    )
    
    remaining_leave_days = fields.Float(
        string='Remaining Leave Balance (Days)',
        compute='_compute_deductions',
        help="Annual leave - leave taken - total deductions"
    )
    
    # Detail Lines
    line_ids = fields.One2many(
        comodel_name='hr.leave.deduction.report.line',
        inverse_name='report_id',
        string='Deduction Details'
    )

    @api.depends('employee_id', 'date_from', 'date_to')
    def _compute_leave_balance(self):
        for record in self:
            if not record.employee_id:
                record.annual_leave_days = 0.0
                record.leave_taken_days = 0.0
                continue
            
            # Get annual leave allocation
            allocation = self.env['hr.leave.allocation'].search([
                ('employee_id', '=', record.employee_id.id),
                ('state', '=', 'validate'),
                ('holiday_status_id.allocation_type', '!=', 'no')
            ], limit=1, order='date_from desc')
            
            record.annual_leave_days = allocation.number_of_days if allocation else 30.0
            
            # Get actual leave taken
            leaves = self.env['hr.leave'].search([
                ('employee_id', '=', record.employee_id.id),
                ('state', '=', 'validate'),
                ('request_date_from', '>=', record.date_from),
                ('request_date_to', '<=', record.date_to)
            ])
            
            record.leave_taken_days = sum(leaves.mapped('number_of_days'))

    @api.depends('employee_id', 'date_from', 'date_to')
    def _compute_deductions(self):
        for record in self:
            if not record.employee_id:
                record.late_deduction_hours = 0.0
                record.late_deduction_days = 0.0
                record.diff_deduction_hours = 0.0
                record.diff_deduction_days = 0.0
                record.absence_deduction_hours = 0.0
                record.absence_deduction_days = 0.0
                record.total_deduction_days = 0.0
                record.remaining_leave_days = 0.0
                continue
            
            # Get attendance sheets for the period
            sheets = self.env['attendance.sheet'].search([
                ('employee_id', '=', record.employee_id.id),
                ('date_from', '>=', record.date_from),
                ('date_to', '<=', record.date_to),
                ('state', 'in', ['confirm', 'done'])
            ])
            
            late_hours = sum(sheets.mapped('tot_late'))
            diff_hours = sum(sheets.mapped('tot_difftime'))
            absence_hours = sum(sheets.mapped('tot_absence'))
            
            # Convert hours to days (assuming 8 hours per day)
            record.late_deduction_hours = late_hours
            record.late_deduction_days = late_hours / 8.0 if late_hours else 0.0
            
            record.diff_deduction_hours = diff_hours
            record.diff_deduction_days = diff_hours / 8.0 if diff_hours else 0.0
            
            record.absence_deduction_hours = absence_hours
            record.absence_deduction_days = absence_hours / 8.0 if absence_hours else 0.0
            
            record.total_deduction_days = (
                record.late_deduction_days +
                record.diff_deduction_days +
                record.absence_deduction_days
            )
            
            record.remaining_leave_days = (
                record.annual_leave_days -
                record.leave_taken_days -
                record.total_deduction_days
            )

    def action_generate_report(self):
        """Generate detailed deduction lines"""
        self.ensure_one()
        
        # Clear existing lines
        self.line_ids.unlink()
        
        # Get attendance sheets
        sheets = self.env['attendance.sheet'].search([
            ('employee_id', '=', self.employee_id.id),
            ('date_from', '>=', self.date_from),
            ('date_to', '<=', self.date_to),
            ('state', 'in', ['confirm', 'done'])
        ], order='date_from')
        
        for sheet in sheets:
            if sheet.tot_late > 0 or sheet.tot_difftime > 0 or sheet.tot_absence > 0:
                self.env['hr.leave.deduction.report.line'].create({
                    'report_id': self.id,
                    'sheet_id': sheet.id,
                    'date_from': sheet.date_from,
                    'date_to': sheet.date_to,
                    'late_hours': sheet.tot_late,
                    'diff_hours': sheet.tot_difftime,
                    'absence_hours': sheet.tot_absence,
                })
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Leave Deduction Report'),
            'res_model': 'hr.leave.deduction.report',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_print_report(self):
        """Print the deduction report"""
        self.ensure_one()
        return self.env.ref('hr_attendance_sheet.action_report_leave_deduction').report_action(self)


class HrLeaveDeductionReportLine(models.TransientModel):
    _name = 'hr.leave.deduction.report.line'
    _description = 'Leave Deduction Report Line'
    _order = 'date_from'

    report_id = fields.Many2one(
        comodel_name='hr.leave.deduction.report',
        string='Report',
        required=True,
        ondelete='cascade'
    )
    sheet_id = fields.Many2one(
        comodel_name='attendance.sheet',
        string='Attendance Sheet',
        readonly=True
    )
    date_from = fields.Date(string='Period From', readonly=True)
    date_to = fields.Date(string='Period To', readonly=True)
    
    late_hours = fields.Float(string='Late (Hours)', readonly=True)
    late_days = fields.Float(
        string='Late (Days)',
        compute='_compute_days',
        store=True
    )
    
    diff_hours = fields.Float(string='Early Out (Hours)', readonly=True)
    diff_days = fields.Float(
        string='Early Out (Days)',
        compute='_compute_days',
        store=True
    )
    
    absence_hours = fields.Float(string='Absence (Hours)', readonly=True)
    absence_days = fields.Float(
        string='Absence (Days)',
        compute='_compute_days',
        store=True
    )
    
    total_deduction_days = fields.Float(
        string='Total Deduction (Days)',
        compute='_compute_days',
        store=True
    )

    @api.depends('late_hours', 'diff_hours', 'absence_hours')
    def _compute_days(self):
        for line in self:
            line.late_days = line.late_hours / 8.0 if line.late_hours else 0.0
            line.diff_days = line.diff_hours / 8.0 if line.diff_hours else 0.0
            line.absence_days = line.absence_hours / 8.0 if line.absence_hours else 0.0
            line.total_deduction_days = line.late_days + line.diff_days + line.absence_days
