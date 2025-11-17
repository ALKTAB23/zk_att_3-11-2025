import pytz
from datetime import datetime, date, timedelta, time
from dateutil.relativedelta import relativedelta
from odoo import models, fields, tools, api, exceptions, _
from odoo.exceptions import UserError, ValidationError
import babel
import calendar
import math

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
TIME_FORMAT = "%H:%M:%S"
import logging

_logger = logging.getLogger(__name__)
import pytz


class attendance_sheet_custom(models.Model):
    _inherit = 'attendance.sheet'

    correct_att_sheet_line_ids = fields.One2many(comodel_name='correct.attendance.sheet.line',
                                                 string='Attendances To Validate', readonly=True,
                                                 inverse_name='att_sheet_id', ondelete='cascade')
    att_sheet_line_ids = fields.One2many(comodel_name='attendance.sheet.line',
                                         string='Attendances', readonly=False,
                                         inverse_name='att_sheet_id', ondelete='cascade')
    att_policy_id = fields.Many2one(comodel_name='hr.attendance.policy',
                                    string="Attendance Policy ", required=False)
    # def __filter_contracts(self):

    # # redefine contract to filter just emplyee contracts
    # contract_id = fields.Many2one(comodel_name="hr.contract", string="", required=True, )
    sheet_action = fields.Selection(string="Sheet Action",
                                    selection=[
                                        ('default', 'Select Action'),
                                        ('no_action', 'No Action'),
                                        ('deduct_leave', 'Deduct from Leave Balance'),
                                        ('deduct_payslip', 'Deduct from Payslip'),
                                    ], required=False, readonly=False, default='default')
    payslip_id = fields.Many2one("hr.payslip", string="Linked Payslip", readonly=True, )
    approve_date = fields.Datetime('Approve Date', )
    no_wd = fields.Integer(compute="calculate_att_data",
                           string="No of Worked Days", readonly=True,
                           store=True)
    tot_wh = fields.Float(compute="calculate_att_data",
                          string="Total Worked Hours", readonly=True,
                          store=True)
    forget_hours = fields.Float(compute="calculate_att_data",
                                string="Total Forget Hours", readonly=True,
                                store=True)
    late_policy_hours = fields.Float(compute="calculate_att_data",
                                     string="Total Late Hours(Policy)", readonly=True,
                                     store=True)
    diff_policy_hours = fields.Float(compute="calculate_att_data",
                                     string="Total Diff Time Hours(Policy)", readonly=True,
                                     store=True)
    no_forget = fields.Integer(compute="calculate_att_data",
                               string="No of Forget", readonly=True,
                               store=True)
    no_leaves = fields.Integer(compute="calculate_att_data",
                               string="No of Leaves", readonly=True,
                               store=True)
    no_leaves_h = fields.Integer(compute="calculate_att_data",
                                 string="No of Leaves(hours)", readonly=True,
                                 store=True)
    leaves_ids = fields.One2many('leaves_report_period', 'sheet_id', string="Leaves Report")
    no_ph = fields.Integer(compute="calculate_att_data",
                           string="No of Public Holidays", readonly=True,
                           store=True)
    default_hr_action = fields.Selection(string="HR Action",
                                         selection=[
                                             ('choose', 'Choose default'),
                                             ('validate', 'To Validate'),

                                             ('apply_policy', 'Apply Policy'),

                                         ],
                                         required=False, readonly=False, default='choose')

    def apply_batch_action(self):
        if self.default_hr_action != 'choose':
            for rec in self.att_sheet_line_ids:
                rec.hr_action = self.default_hr_action

    @api.onchange('employee_id', 'date_from', 'date_to')
    def onchange_employee(self):
        if (not self.employee_id) or (not self.date_from) or (not self.date_to):
            return
        employee = self.employee_id
        date_from = self.date_from
        date_to = self.date_to
        ttyme = datetime.combine(fields.Date.from_string(date_from), time.min)
        locale = self.env.context.get('lang', 'en_US')
        if locale == "ar_SY":
            locale = "ar"
        self.name = _('Attendance Sheet of %s for %s') % (employee.name,
                                                          tools.ustr(
                                                              babel.dates.format_date(
                                                                  date=ttyme,
                                                                  format='MMMM-y',
                                                                  locale=locale)))
        self.company_id = employee.company_id
        contract_ids = self.env['hr.payslip'].get_contract(employee, date_from,
                                                           date_to)
        if not contract_ids:
            return
        for con in contract_ids:
            # check to filter if this contract is primary contract
            contract_id = self.env['hr.contract'].browse(con)
            if contract_id.type_id.is_primary:
                self.contract_id = contract_id

    def get_time_from_float(self, float_type):
        str_off_time = str(float_type)
        official_hour = str_off_time.split('.')[0]
        official_minute = int(round(round(float("0." + str_off_time.split('.')[1]), 4) * 60))
        str_off_time = official_hour + ":" + str(official_minute)
        str_off_time = datetime.strptime(str_off_time, "%H:%M").time()
        return str_off_time

    def _get_float_from_time(self, time):
        time_type = datetime.strftime(time, "%H:%M:%S")
        signOnP = [int(n) for n in time_type.split(":")]
        signOnH = signOnP[0] + signOnP[1] / 60.0 + signOnP[2] / 3600
        return signOnH

    def get_public_holiday2(self, date, emp):
        public_holiday = []
        public_holidays = self.env['hr.public.holiday'].sudo().search(
            [('date_from', '<=', str(date)), ('date_to', '>=', str(date)),
             ('state', '=', 'active')])
        _logger.info(">>>>>>ph>>" + str(public_holidays) + "_" + str(date))
        for ph in public_holidays:
            print('ph is', ph.name, [e.name for e in ph.emp_ids])
            public_holiday.append(ph.id)

        return public_holiday

    def get_attendances(self):
        self.env['resource.calendar'].update_shifts()
        for att_sheet in self:
            att_sheet.att_sheet_line_ids.unlink()
            att_sheet.correct_att_sheet_line_ids.unlink()
            att_line = self.env["attendance.sheet.line"]
            lv_hours = 0.0
            from_date = att_sheet.date_from
            to_date = att_sheet.date_to
            emp = att_sheet.employee_id

            number_days = (to_date - from_date).days + 1
            all_dates = [(from_date + timedelta(days=x)) for x in
                         range((to_date - from_date).days + 1)]
            att_rec_not_process = self.env['hr.attendance'].search(
                [('sheet_id', '=', False), ('employee_id', '=', emp.id)], order="check_in")
            for day in all_dates:
                date = day.strftime('%Y-%m-%d %H:%M:%S')
                match_shift = self.env['zk.machine'].get_match_shift(str(date), att_sheet.employee_id.id)
                date = day.strftime('%Y-%m-%d')
                if match_shift:
                    if match_shift.hr_shift.day_period == 'rest':
                        continue
                    tz = pytz.timezone(match_shift.schedule_id.tz)
                    attendance_rec = self.env['schedule_attendances'].browse(match_shift.id)
                    is_absent = True
                    for att_rec in att_rec_not_process:
                        if str(att_rec.check_in.date()) == str(date):
                            is_absent = False
                            tz = pytz.timezone(attendance_rec.schedule_id.tz)
                            checkin_utc = pytz.utc.localize(att_rec.check_in).astimezone(tz).replace(tzinfo=None)

                            if not att_rec.check_out:
                                ex_hour_from = str(self.get_time_from_float(att_rec.match_shift.hour_from))
                                chour = int(ex_hour_from.split(":")[0])
                                cminute = int(ex_hour_from.split(":")[1])
                                attend_date_now = datetime.strptime(str(checkin_utc), '%Y-%m-%d %H:%M:%S')
                                expect_check_in = datetime(attend_date_now.date().year, attend_date_now.date().month,
                                                           attend_date_now.date().day, chour, cminute, 0)

                                totalminutes = (checkin_utc - expect_check_in).total_seconds() / 60.0
                                if totalminutes > 60:
                                    values = [(0, 0, {
                                        'date': date,
                                        'day': str(day.weekday()),
                                        'pl_sign_in': att_rec.match_shift.hour_from,
                                        'pl_sign_out': att_rec.match_shift.hour_to,
                                        'ac_sign_in': False,
                                        'ac_sign_out': self._get_float_from_time(checkin_utc),
                                        'late_in': 0,
                                        'act_late_in': att_rec.act_delay_time,
                                        'act_diff_time': att_rec.act_diff_time,
                                        'diff_time': 0,
                                        'overtime': att_rec.act_over_time,
                                        'att_sheet_id': att_sheet.id,
                                        'line_att_policy_id': attendance_rec.att_policy_id.id,
                                        'worked_hours': att_rec.worked_hours,
                                        'status': 'no_checkin',
                                        'hr_action': 'validate',
                                        'note': ''
                                    })]
                                    att_sheet.att_sheet_line_ids = values
                                else:
                                    values = [(0, 0, {
                                        'date': date,
                                        'day': str(day.weekday()),
                                        'pl_sign_in': att_rec.match_shift.hour_from,
                                        'pl_sign_out': att_rec.match_shift.hour_to,
                                        'ac_sign_in': self._get_float_from_time(checkin_utc),
                                        'ac_sign_out': False,
                                        'act_late_in': att_rec.act_delay_time,
                                        'late_in': 0,
                                        'act_diff_time': att_rec.act_diff_time,
                                        'diff_time': 0,
                                        'overtime': att_rec.act_over_time,
                                        'att_sheet_id': att_sheet.id,
                                        'line_att_policy_id': attendance_rec.att_policy_id.id,
                                        'worked_hours': att_rec.worked_hours,
                                        'status': 'no_checkout',
                                        'hr_action': 'validate',
                                        'note': ''
                                    })]
                                    att_sheet.att_sheet_line_ids = values
                            else:

                                checkout_utc = pytz.utc.localize(att_rec.check_out).astimezone(tz).replace(tzinfo=None)
                                # check if employee get leave of half day or custom hours within a day
                                in_leaves = self.env['hr.leave'].search([('holiday_type', '=', 'employee'),
                                                                         ('employee_id', '=', self.employee_id.id),
                                                                         ('request_date_from', '<=', date),
                                                                         ('request_date_to', '>=', date),
                                                                         ('state', '=', 'validate')])
                                ded_delay_exclude_leave = 0
                                for lv in in_leaves:
                                    if lv.request_unit_half:

                                        ded_delay_exclude_leave = att_rec.match_shift.schedule_id.hours_per_day / 2
                                    else:
                                        if lv.request_unit_hours:
                                            ded_delay_exclude_leave = float(lv.request_hour_to) - float(
                                                lv.request_hour_from)

                                delay_calc = att_rec.act_delay_time - ded_delay_exclude_leave
                                if delay_calc < 0:
                                    delay_calc = 0
                                values = [(0, 0, {
                                    'date': date,
                                    'day': str(day.weekday()),
                                    'pl_sign_in': att_rec.match_shift.hour_from,
                                    'pl_sign_out': att_rec.match_shift.hour_to,
                                    'ac_sign_in': self._get_float_from_time(checkin_utc),
                                    'ac_sign_out': self._get_float_from_time(checkout_utc),
                                    'act_late_in': delay_calc,
                                    'late_in': 0,
                                    'act_diff_time': att_rec.act_diff_time,
                                    'diff_time': 0,
                                    'overtime': att_rec.act_over_time,
                                    'worked_hours': att_rec.worked_hours,
                                    'att_sheet_id': att_sheet.id,
                                    'line_att_policy_id': att_rec.att_shift_rec.att_policy_id.id,
                                    'status': 'ready',
                                    'note': ''
                                })]
                                att_sheet.correct_att_sheet_line_ids = values
                    if is_absent:
                        in_leave = self.env['hr.leave'].search([('holiday_type', '=', 'employee'),
                                                                ('employee_id', '=', self.employee_id.id),
                                                                ('request_date_from', '<=', date),
                                                                ('request_date_to', '>=', date),
                                                                ('state', '=', 'validate')])
                        absent_in_leave = 'ab'
                        if in_leave:
                            absent_in_leave = 'leave'
                        # if in_leave.request_unit_half or in_leave.request_unit_hours:
                        #     absent_in_leave='leave_h'
                        #     lv_hours=in_leave.number_of_hours_display

                        c_date = datetime(day.year, day.month, day.day)
                        ph_leaves = att_sheet.get_public_holiday2(c_date.date(), self.employee_id)
                        if ph_leaves:
                            absent_in_leave = 'ph'
                        values = [(0, 0, {
                            'date': date,
                            'day': str(day.weekday()),
                            'pl_sign_in': attendance_rec.hr_shift.hour_from,
                            'pl_sign_out': attendance_rec.hr_shift.hour_to,
                            'ac_sign_in': False,
                            'ac_sign_out': False,
                            'act_late_in': 0.0,
                            'act_diff_time': 0.0,
                            'late_in': 0,
                            'diff_time': 0,
                            'overtime': 0.0,
                            # 'leave_hours':lv_hours,
                            'att_sheet_id': att_sheet.id,
                            'line_att_policy_id': attendance_rec.att_policy_id.id,
                            'status': absent_in_leave,
                            'hr_action': 'validate',
                            'note': ''
                        })]
                        att_sheet.att_sheet_line_ids = values

    def action_attsheet_confirm(self):
        for att_sheet in self:
            if att_sheet.att_sheet_line_ids:
                for att in att_sheet.att_sheet_line_ids:
                    if att.hr_action == 'validate':
                        raise ValidationError(_('Please validate attendance records before submit to manager!'))
            for att in att_sheet.att_sheet_line_ids:
                att_sheet.correct_att_sheet_line_ids = [(0, 0, {
                    'date': att.date,
                    'day': att.day,
                    'pl_sign_in': att.pl_sign_in,
                    'pl_sign_out': att.pl_sign_out,
                    'ac_sign_in': att.ac_sign_in,
                    'ac_sign_out': att.ac_sign_in,
                    'act_late_in': att.act_late_in,
                    'act_diff_time': att.act_diff_time,
                    'late_in': 0,
                    'diff_time': 0,
                    'overtime': att.overtime,
                    'att_sheet_id': att.att_sheet_id.id,
                    'line_att_policy_id': att.line_att_policy_id.id,
                    'status': att.status,
                    'hr_action': att.hr_action,
                    'note': ''
                })]

            att_sheet.calculate_att_data()
            att_sheet.write({'state': 'confirm'})

    def action_attsheet_approve(self):
        for sheet in self:
            if sheet.sheet_action != 'default':
                sheet.create_payslip()
                sheet.approve_date = fields.Datetime.now()
                sheet.write({'state': 'done'})
            else:
                raise UserError(_("Please Choose Action!"))

    def create_payslip(self):
        payslips = self.env['hr.payslip']
        for att_sheet in self:
            if att_sheet.payslip_id:
                continue

            from_date = att_sheet.date_from
            to_date = att_sheet.date_to
            employee = att_sheet.employee_id
            slip_data = self.env['hr.payslip'].onchange_employee_id(from_date,
                                                                    to_date,
                                                                    employee.id,
                                                                    contract_id=False, sheet_id=att_sheet)
            contract_id = slip_data['value'].get('contract_id')
            if not contract_id:
                raise exceptions.UserError(
                    'There is No Contracts for %s That covers the period of the Attendance sheet' % employee.name)

            worked_days_line_ids = slip_data['value'].get(
                'worked_days_line_ids')

            overtime = []
            if  att_sheet.no_overtime:
                overtime.append({
                        'name': "Overtime",
                        'code': 'OVT',
                        'contract_id': contract_id,
                        'sequence': 30,
                        'number_of_days': att_sheet.no_overtime,
                        'number_of_hours': att_sheet.tot_overtime,
                })

            if att_sheet.sheet_action == 'deduct_leave':
                leave_balance = att_sheet._calculate_remaining_leaves()

                if att_sheet.employee_id.resource_calendar_ids:
                    avg_hours = att_sheet.employee_id.resource_calendar_ids.hours_per_day
                else:
                    avg_hours = 0

                total_deduct_days = 0
                if leave_balance and att_sheet.no_absence:
                    hours_per_day = att_sheet.tot_absence / att_sheet.no_absence
                    deduct_days = min(leave_balance, att_sheet.no_absence)
                    att_sheet.no_absence -= deduct_days
                    att_sheet.tot_absence -= deduct_days * hours_per_day
                    leave_balance -= deduct_days
                    total_deduct_days += deduct_days

                if leave_balance and att_sheet.late_policy_hours:
                    deduct_days = min(leave_balance, (att_sheet.late_policy_hours / avg_hours if avg_hours > 0 else 8))
                    att_sheet.late_policy_hours -= (deduct_days * avg_hours if avg_hours > 0 else 8)
                    leave_balance -= deduct_days
                    total_deduct_days += deduct_days

                if leave_balance and att_sheet.diff_policy_hours:
                    deduct_days = min(leave_balance, (att_sheet.diff_policy_hours / avg_hours if avg_hours > 0 else 8))
                    att_sheet.diff_policy_hours -= (deduct_days * avg_hours if avg_hours > 0 else 8)
                    leave_balance -= deduct_days
                    total_deduct_days += deduct_days

                if leave_balance and att_sheet.forget_hours:
                    deduct_days = min(leave_balance, (att_sheet.forget_hours / avg_hours if avg_hours > 0 else 8))
                    att_sheet.forget_hours -= (deduct_days * avg_hours if avg_hours > 0 else 8)
                    leave_balance -= deduct_days
                    total_deduct_days += deduct_days

                print("total_deduct_days...", total_deduct_days)
                if total_deduct_days:
                    holiday_ids = [x.id for x in
                                   self.env['hr.leave.type'].search(
                                       [('requires_allocation', '=', 'yes'), ('attendance_deduct', '=', True)])]
                    domain = [('employee_id', '=', att_sheet.employee_id.id), ('state', '=', 'validate'),
                              ('holiday_status_id', 'in', holiday_ids)]
                    leave_allocation_ids = self.env['hr.leave.allocation'].search(domain)

                    for leave_allocation in leave_allocation_ids:
                        if total_deduct_days <= 0:
                            break

                        if leave_allocation.allocation_type == 'regular':
                            if leave_allocation.number_of_days <= total_deduct_days:
                                reconcile_days = leave_allocation.number_of_days
                                total_deduct_days -= reconcile_days
                                leave_allocation.action_refuse()
                                leave_allocation.att_sheet_id = att_sheet
                                continue

                        reconcile_days = min(leave_allocation.number_of_days, total_deduct_days)
                        leave_allocation.number_of_days -= reconcile_days
                        total_deduct_days -= reconcile_days
                        leave_allocation.att_sheet_id = att_sheet
                        leave_allocation.att_sheet_deduct = reconcile_days

            absence = [{
                'name': "Absence",
                'code': 'ABS',
                'contract_id': contract_id,
                'sequence': 35,
                'number_of_days': att_sheet.no_absence,
                'number_of_hours': att_sheet.tot_absence,
            }]
            late = [{
                'name': "Late In",
                'code': 'LATE',
                'contract_id': contract_id,
                'sequence': 40,
                'number_of_days': att_sheet.no_late,
                'number_of_hours': att_sheet.late_policy_hours,
            }]
            difftime = [{
                'name': "Difference time",
                'code': 'DIFFT',
                'contract_id': contract_id,
                'sequence': 45,
                'number_of_days': att_sheet.no_difftime,
                'number_of_hours': att_sheet.diff_policy_hours,
            }]
            frgttime = [{
                'name': "Forget Attendance time",
                'code': 'FRGT',
                'contract_id': contract_id,
                'sequence': 50,
                'number_of_days': att_sheet.no_forget,
                'number_of_hours': att_sheet.forget_hours,
            }]

            worked_days_line_ids += late + absence + difftime + frgttime + overtime
            res = {
                'employee_id': employee.id,
                'name': slip_data['value'].get('name'),
                'struct_id': slip_data['value'].get('struct_id'),
                'contract_id': contract_id,
                'input_line_ids': [(0, 0, x) for x in
                                   slip_data['value'].get('input_line_ids')],
                'worked_days_line_ids': [(0, 0, x) for x in
                                         worked_days_line_ids],
                'date_from': from_date,
                'date_to': to_date,
            }

            new_payslip = self.env['hr.payslip'].create(res)
            att_sheet.payslip_id = new_payslip
            payslips += new_payslip
        return payslips

    def _calculate_remaining_leaves(self):
        for rec in self:
            holiday_ids = [x.id for x in self.env['hr.leave.type'].search(
                [('requires_allocation', '=', 'yes'), ('attendance_deduct', '=', True)])]
            domain = [('employee_id', '=', rec.employee_id.id), ('state', '=', 'validate'),
                      ('holiday_status_id', 'in', holiday_ids)]
            leave_allocation_ids = self.env['hr.leave.allocation'].search(domain)

            emp_allocations = sum([x.number_of_days for x in leave_allocation_ids])
            emp_leaves = sum([x.number_of_days for x in self.env['hr.leave'].sudo().search(domain)])
            balance = emp_allocations - emp_leaves
            return balance

    def action_attsheet_draft(self):
        res = super().action_attsheet_draft()

        leave_allocation_ids = self.env['hr.leave.allocation'].search([('att_sheet_id', '=', self.id)])
        for leave_allocation in leave_allocation_ids:
            if leave_allocation.allocation_type == 'regular' and leave_allocation.state == 'refuse':
                leave_allocation.action_draft()
                leave_allocation.action_confirm()
                leave_allocation.action_validate()
                leave_allocation.att_sheet_id = None
                continue

            leave_allocation.number_of_days += leave_allocation.att_sheet_deduct
            leave_allocation.att_sheet_id = None
            leave_allocation.att_sheet_deduct = None

        return res

    def get_schedule(self, contract_id, current_date):
        schedules = contract_id.shift_schedule
        match_schedules = schedules.search(
            [('start_date', '<=', str(current_date)), ('active', '=', True), ('rel_hr_schedule', '=', contract_id.id)])
        active_schedule_id = False
        sft_start_date = False
        for sc in match_schedules:
            if sc.end_date:
                sc_end_date = datetime(sc.end_date.year, sc.end_date.month, sc.end_date.day)
                if current_date.date() <= sc_end_date.date():
                    active_schedule_id = sc.hr_shift
            else:
                active_schedule_id = sc.hr_shift
        return active_schedule_id

    def calculate_att_data(self):
        overtime = 0
        no_overtime = 0
        late = 0
        no_late = 0
        diff = 0
        no_diff = 0
        tot_wh = 0
        no_wd = 0
        absence_hours = 0
        no_absence = 0
        no_forget = 0
        forget_hours = 0
        no_leaves = 0
        no_leaves_h = 0
        no_ph = 0
        avg_hour = 0
        late_policy = 0
        diff_policy = 0
        for att_sheet in self:
            for line in att_sheet.correct_att_sheet_line_ids:
                ddate = datetime(att_sheet.date_from.year, att_sheet.date_from.month, att_sheet.date_from.day)
                wshedule = self.get_schedule(att_sheet.contract_id, ddate)
                if wshedule:
                    avg_hour = wshedule.hours_per_day
                no_plicy_flag = True
                if line.overtime > 0 and line.date:
                    # Apply Overtime Policy
                    policy = line.line_att_policy_id
                    current_rule = False
                    date_str = str(datetime.combine(line.date, time.min)) if line.date else False
                    match_shift = self.env['zk.machine'].get_match_shift(date_str, att_sheet.employee_id.id)
                    shift = match_shift.hr_shift.day_period if match_shift else False
                    if shift == 'weekend':
                        status_to_compare = shift
                    else:
                        status_to_compare = 'workday' if line.status == 'ready' else line.status
                    for rule in policy.overtime_rule_ids.filtered(lambda l: l.type == status_to_compare):
                        current_rule = rule
                    # ✅ تطبيق قواعد الإضافي بشكل صحيح
                    if current_rule:
                        # active_after هو مدة (بالساعات)، نقارنه مع مدة الإضافي
                        if line.overtime >= current_rule.active_after:
                            no_overtime += 1
                            overtime += (line.overtime * current_rule.rate)
                            _logger.info(f"✅ Overtime: {line.overtime}h × Rate {current_rule.rate} = {line.overtime * current_rule.rate}h")
                        else:
                            _logger.info(f"⚠️ Overtime {line.overtime}h < threshold {current_rule.active_after}h")
                    elif line.overtime > 0:
                        no_overtime += 1
                        overtime += line.overtime
                        _logger.info(f"📊 Overtime without rule: {line.overtime}h")
                no_plicy_flag = True
                if line.status == "ab":
                    no_absence += 1

                    # Apply Absetn Policy
                    policy = line.line_att_policy_id
                    flag = True
                    for rule in policy.absence_rule_id.line_ids:
                        if rule.counter == str(no_absence):
                            _logger.info("__===^^^^^^^^^^^^^^_" + str(rule.rate))
                            flag = False
                            absence_hours += (avg_hour * rule.rate)
                    if flag:
                        absence_hours += avg_hour
                if line.act_diff_time > 0:

                    # Apply Diff Policy
                    policy = line.line_att_policy_id
                    last_counter = 0
                    for rule in policy.diff_rule_id.line_ids:
                        if last_counter < int(rule.counter):
                            last_counter = int(rule.counter)

                    for rule in policy.diff_rule_id.line_ids:
                        if rule.counter == str(no_diff) and (
                                line.act_diff_time >= rule.time and line.act_diff_time <= rule.time_limit):
                            no_plicy_flag = False
                            if rule.type == 'fix':
                                diff_policy += rule.amount
                                line.diff_time = rule.amount
                            else:
                                if rule.type == 'rate':
                                    diff_policy += (line.act_diff_time * rule.rate)
                                    line.diff_time = (line.act_diff_time * rule.rate)
                                else:
                                    if rule.type == 'rate_fix':
                                        diff_policy += (line.act_diff_time * rule.rate) + rule.amount
                                        line.diff_time = (line.act_diff_time * rule.rate) + rule.amount
                    if last_counter > no_diff:
                        no_diff += 1
                    if no_plicy_flag:
                        diff += line.act_diff_time
                        line.diff_time = 0
                if line.act_late_in > 0:

                    # Apply Late Policy
                    policy = line.line_att_policy_id
                    no_plicy_flag = True
                    last_counter = 0
                    for rule in policy.late_rule_id.line_ids:
                        if last_counter < int(rule.counter):
                            last_counter = int(rule.counter)
                    _logger.info("__===^^^^^^^^^^^^^^last=_" + str(last_counter))
                    for rule in policy.late_rule_id.line_ids:
                        if rule.counter == str(no_late) and (
                                line.act_late_in >= rule.time and line.act_late_in <= rule.time_limit):
                            no_plicy_flag = False
                            _logger.info("__===^^^^^^^^^^^^^^last=_" + str(last_counter) + "_" + str(no_late))
                            if rule.type == 'fix':
                                late_policy += rule.amount
                                line.late_in = rule.amount
                            else:
                                if rule.type == 'rate':
                                    late_policy += (line.act_late_in * rule.rate)
                                    line.late_in = (line.act_late_in * rule.rate)
                                else:
                                    if rule.type == 'rate_fix':
                                        late_policy += (line.act_late_in * rule.rate) + rule.amount
                                        line.late_in = (line.act_late_in * rule.rate) + rule.amount
                    if last_counter > no_late:
                        no_late += 1
                    if no_plicy_flag:
                        late += line.act_late_in
                        line.late_in = 0
                if line.status == 'no_checkin' or line.status == 'no_checkout':
                    no_forget += 1
                    # Apply Late Policy
                    policy = line.line_att_policy_id
                    for rule in policy.forget_rule_id.line_ids:
                        if rule.counter == str(no_forget):
                            forget_hours += (avg_hour * rule.rate)
                if line.status == 'leave':
                    no_leaves += 1
                if line.status == 'ph':
                    no_ph += 1
                if line.worked_hours > 0:
                    tot_wh += line.worked_hours
                    no_wd += 1
            # for line in att_sheet.correct_att_sheet_line_ids:

            in_leaver = self.env['hr.leave'].search([
                ('employee_id', '=', self.employee_id.id),
                ('request_date_from', '>=', att_sheet.date_from),

                ('state', '=', 'validate')])
            for lvv in in_leaver:
                if lvv.request_unit_half or lvv.request_unit_hours:
                    no_leaves_h += lvv.number_of_hours_display
            leave_dict = []
            leave_types = self.env['hr.leave.type'].search([])
            for r in self.leaves_ids:
                r.unlink()
            for ltype in leave_types:
                total_days_c = 0
                total_hours_c = 0
                in_leaver = self.env['hr.leave'].search([('holiday_status_id', '=', ltype.id),
                                                         ('employee_id', '=', self.employee_id.id),
                                                         ('request_date_from', '>=', att_sheet.date_from),

                                                         ('state', '=', 'validate')])
                logging.info("Leave=" + str(in_leaver) + "_" + str(ltype.id) + "_" + str(att_sheet.date_from))
                for lv in in_leaver:
                    if lv.request_unit_half or lv.request_unit_hours:
                        logging.info(
                            "hours>>>>" + str(lv.number_of_days_display) + "_h_" + str(lv.number_of_hours_display))
                        total_hours_c += lv.number_of_hours_display
                    else:
                        logging.info("days>>>>")
                        total_days_c += lv.number_of_days_display
                leave_values = [(0, 0, {
                    'leave_type': ltype.id,
                    'total_days': total_days_c,
                    'total_hours': total_hours_c,
                })]
                self.leaves_ids = leave_values
            values = {
                'tot_overtime': overtime,
                'no_overtime': no_overtime,
                'tot_difftime': diff,
                'no_difftime': no_diff,
                'no_absence': no_absence,
                'tot_absence': absence_hours,
                'tot_late': late,
                'no_late': no_late,
                'tot_wh': tot_wh,
                'no_wd': no_wd,
                'no_forget': no_forget,
                'forget_hours': forget_hours,
                'late_policy_hours': late_policy,
                'diff_policy_hours': diff_policy,
                'no_leaves': no_leaves,
                'no_leaves_h': no_leaves_h,
                'no_ph': no_ph,
            }
            att_sheet.write(values)


class attendance_sheet_line_custom(models.Model):
    _inherit = 'attendance.sheet.line'
    day = fields.Selection([
        ('5', 'Saterday'),
        ('6', 'Sunday'),
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday')
    ], 'Day of Week', required=True, index=True, )
    status = fields.Selection(string="Status",
                              selection=[('ab', 'Absence'),
                                         ('no_checkout', 'No Checkout'),  # no checkout
                                         ('no_checkin', 'No Checkin'),  # no checkin
                                         ('ready', 'Ready'),
                                         ('ph', 'Public Holiday'),
                                         ('leave', 'Leave'),
                                         ('leave_h', 'Leave(hours)'),
                                         ('compensate', 'Compensate Request'),
                                         ],
                              required=False, readonly=False, default='need_action')
    hr_action = fields.Selection(string="HR Action",
                                 selection=[
                                     ('validate', 'To Validate'),

                                     ('apply_policy', 'Apply Policy'),

                                 ],
                                 required=False, readonly=False, default='apply_policy')
    line_att_policy_id = fields.Many2one(comodel_name='hr.attendance.policy',
                                         string="Policy ", required=False)


class correct_attendance_sheet_line_custom(models.Model):
    _name = 'correct.attendance.sheet.line'
    _inherit = 'attendance.sheet.line'


class leaves_report_period_class(models.Model):
    _name = "leaves_report_period"
    sheet_id = fields.Many2one('attendance.sheet')
    leave_type = fields.Many2one('hr.leave.type', 'Leave Type', required=True)
    total_days = fields.Float('Total Days', default=0.0)
    total_hours = fields.Float('Total Hours', default=0.0)


# >>>>>>>>>>>>>>>>>>>>>>Batch Attendance Sheet >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
class batch_attendance_sheet__custom(models.Model):
    _name = 'batch.attendance.sheet'

    name = fields.Char(string="Batch Name", required=True)
    date_from = fields.Date(string='Date From', readonly=True, required=True,
                            default=lambda self: fields.Date.to_string(
                                date.today().replace(day=1)), )
    date_to = fields.Date(string='Date To', readonly=True, required=True,
                          default=lambda self: fields.Date.to_string(
                              (datetime.now() + relativedelta(months=+1, day=1,
                                                              days=-1)).date()))
    filter_option = fields.Selection([
        ('dept_tags', 'Departments and Tags'),
        ('emp', 'Department and Employees'),
    ], string="Filter By:", default='dept_tags')
    category_ids = fields.Many2many('hr.employee.category', string="Tags", help="Employee Tags")
    department_ids = fields.Many2many('hr.department', string='Departments', help="Departments")
    employee_ids = fields.Many2many('hr.employee', string="Employees", help="Employees")
    records_to_validate = fields.One2many('attendance.sheet.to_validate', 'batch_id',
                                          string='Employees Attendance Sheet', ondelete='cascade')
    records_to_approve = fields.One2many('attendance.sheet.to_approve', 'batch_id', string='Employees Attendance Sheet',
                                         ondelete='cascade')
    records_approved = fields.One2many('attendance.sheet.approved', 'batch_id', string='Employees Attendance Sheet',
                                       ondelete='cascade')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('done', 'Approved')], default='draft', track_visibility='onchange',
        string='Status', required=True, readonly=True, index=True,
        help=' * The \'Draft\' status is used when a HR user is creating a new  attendance sheet. '
             '\n* The \'Confirmed\' status is used when  attendance sheet is confirmed by HR user.'
             '\n* The \'Approved\' status is used when  attendance sheet is accepted by the HR Manager.')
    default_sheet_action = fields.Selection(string="Batch default Sheet Action",
                                            selection=[
                                                ('default', 'Select Action'),
                                                ('no_action', 'No Action'),
                                                ('deduct_leave', 'Deduct from Leave Balance'),
                                                ('deduct_payslip', 'Deduct from Payslip'),
                                            ], required=False, readonly=False, default='default')

    def unlink(self):
        if any(self.filtered(
                lambda att: att.state not in ('draft', 'confirm'))):
            raise UserError(_(
                'You cannot delete batch an attendance sheet which is not draft or confirmed!'))
        return super(batch_attendance_sheet__custom, self).unlink()

    def action_attsheet_draft(self):
        if self.payslip_id:
            self.payslip_id.action_payslip_cancel()
        self.write({'state': 'draft'})

    def batch_action_attsheet_confirm(self, sheet_obj):
        for att_sheet in sheet_obj:
            att_sheet.get_attendances()
            if att_sheet.att_sheet_line_ids:
                _logger.info("____in batch ___")
                for att in att_sheet.att_sheet_line_ids:
                    if att.hr_action == 'validate':
                        return False
            att_sheet.calculate_att_data()
            att_sheet.write({'state': 'confirm'})
        return True

    def get_attendances_sheets(self):
        employee_list = []
        if self.filter_option == 'dept_tags':
            if self.department_ids and not self.category_ids:
                for dept in self.department_ids:
                    dept_contracts_ids = self.env['hr.contract'].search(
                        [('department_id', 'child_of', self.department_ids.ids), ('state', '=', 'open')])
                    for con in dept_contracts_ids:
                        # get only employee contract to calcuate attendance sheets
                        if con.type_id.is_primary:
                            employee_list.append({'emp_id': con.employee_id.id, 'contract_id': con.id})
            else:
                if self.category_ids and not self.department_ids:
                    employees = self.env['hr.employee'].search([('category_ids', 'in', self.category_ids.ids)])
                    contracts = self.env['hr.contract'].search(
                        [('employee_id', 'in', employees.ids), ('state', '=', 'open')])
                    for con in contracts:
                        # get only employee contract to calcuate attendance sheets
                        if con.type_id.is_primary:
                            employee_list.append({'emp_id': con.employee_id.id, 'contract_id': con.id})
                else:
                    if self.category_ids and not self.department_ids:
                        employees = self.env['hr.employee'].search([('category_ids', 'in', self.category_ids.ids)])
                        contracts = self.env['hr.contract'].search(
                            [('employee_id', 'in', employees.ids), ('state', '=', 'open')])
                        # emp_sheets=self.env['attendance.sheet'].search([('employee_id.contract_id','in',contracts.ids),('date_from','=',self.date_from),('date_to','=',self.date_to)])
                        for con in contracts:
                            # get only employee contract to calcuate attendance sheets
                            if con.type_id.is_primary:
                                employee_list.append({'emp_id': con.employee_id.id, 'contract_id': con.id})

        else:
            if self.filter_option == 'emp':
                if self.employee_ids:
                    _logger.info("_employeess==" + str(self.employee_ids.ids))
                    contracts = self.env['hr.contract'].search(
                        [('employee_id', 'in', self.employee_ids.ids), ('state', '=', 'open')])
                    # emp_sheets=self.env['attendance.sheet'].search([('employee_id.contract_id','in',contracts.ids),('date_from','=',self.date_from),('date_to','=',self.date_to)])
                    for con in contracts:
                        # get only employee contract to calcuate attendance sheets
                        if con.type_id.is_primary:
                            employee_list.append({'emp_id': con.employee_id.id, 'contract_id': con.id})
                else:
                    if self.department_ids:
                        for dept in self.department_ids:
                            dept_contracts_ids = self.env['hr.contract'].search(
                                [('department_id', 'child_of', self.department_ids.ids), ('state', '=', 'open')])

                            for con in dept_contracts_ids:
                                # get only employee contract to calcuate attendance sheets
                                if con.type_id.is_primary:
                                    employee_list.append({'emp_id': con.employee_id.id, 'contract_id': con.id})

        for emp in employee_list:
            values = {
                'employee_id': emp['emp_id'],
                'contract_id': emp['contract_id'],
                'date_from': self.date_from,
                'date_to': self.date_to,
            }
            check_att = self.env['hr.attendance'].search(
                [('employee_id', '=', emp['emp_id']), ('check_in', '>=', self.date_from)], limit=1)
            sheet_obj = False
            if check_att:
                sheet_search = self.env['attendance.sheet'].search(
                    [('employee_id', '=', emp['emp_id']), ('date_from', '>=', self.date_from),
                     ('date_to', '<=', self.date_to)], limit=1)
                if not sheet_search:
                    sheet_obj = self.env['attendance.sheet'].create(values)

                    employee = check_att[0].employee_id
                    date_from = self.date_from
                    date_to = self.date_to
                    ttyme = datetime.combine(fields.Date.from_string(date_from), time.min)
                    locale = self.env.context.get('lang', 'en_US')
                    if locale == "ar_SY":
                        locale = "ar"
                    sheet_obj.name = _('Attendance Sheet of %s for %s') % (employee.name,
                                                                           tools.ustr(
                                                                               babel.dates.format_date(
                                                                                   date=ttyme,
                                                                                   format='MMMM-y',
                                                                                   locale=locale)))
                    if self.batch_action_attsheet_confirm(sheet_obj):
                        values = [(0, 0, {
                            'employee_id': sheet_obj.employee_id.id,
                            'sheet_ids_to_approve': [(4, sheet_obj.id)],
                        })]
                        self.records_to_approve = values
                    else:
                        values = [(0, 0, {
                            'employee_id': sheet_obj.employee_id.id,
                            'sheet_ids_to_validate': [(4, sheet_obj.id)],
                        })]
                        self.records_to_validate = values
                    self.state = 'confirm'

    def action_attsheet_confirm(self):
        for att_sheet in self:
            if att_sheet.records_to_validate:
                for sh in att_sheet.records_to_validate:
                    complete = True
                    for att in sh.sheet_ids_to_validate[0].att_sheet_line_ids:
                        if att.hr_action == 'validate':
                            complete = False

                    if complete:
                        if sh.sheet_ids_to_validate[0].state != 'confirm':
                            for att in sh.sheet_ids_to_validate[0].att_sheet_line_ids:
                                att.att_sheet_id.correct_att_sheet_line_ids = [(0, 0, {
                                    'date': att.date,
                                    'day': att.day,
                                    'pl_sign_in': att.pl_sign_in,
                                    'pl_sign_out': att.pl_sign_out,
                                    'ac_sign_in': att.ac_sign_in,
                                    'ac_sign_out': att.ac_sign_in,
                                    'act_late_in': att.act_late_in,
                                    'act_diff_time': att.diff_time,
                                    'late_in': att.late_in,
                                    'diff_time': att.diff_time,
                                    'overtime': att.overtime,
                                    'att_sheet_id': att.att_sheet_id.id,
                                    'line_att_policy_id': att.line_att_policy_id.id,
                                    'status': att.status,
                                    'hr_action': att.hr_action,
                                    'note': ''
                                })]
                            sh.sheet_ids_to_validate[0].calculate_att_data()
                            sh.sheet_ids_to_validate[0].write({'state': 'confirm'})

                        values = [(0, 0, {
                            'employee_id': sh.employee_id.id,
                            'sheet_ids_to_approve': [(4, sh.sheet_ids_to_validate[0].id)],
                        })]
                        att_sheet.records_to_approve = values
                        sh.unlink()

    def action_attsheet_approve(self):
        for att_sheet in self:
            if att_sheet.records_to_approve:
                for sh in att_sheet.records_to_approve:
                    if att_sheet.default_sheet_action and att_sheet.default_sheet_action != 'default':
                        sh.sheet_ids_to_approve[0].sheet_action = att_sheet.default_sheet_action
                    sh.sheet_ids_to_approve[0].action_attsheet_approve()
                    values = [(0, 0, {
                        'employee_id': sh.employee_id.id,
                        'sheet_ids_approved': [(4, sh.sheet_ids_to_approve[0].id)],
                    })]
                    att_sheet.records_approved = values
                    sh.unlink()
            if not att_sheet.records_to_approve and not att_sheet.records_to_validate:
                att_sheet.state = 'done'


class batch_to_validate_attendance_sheet(models.Model):
    _name = 'attendance.sheet.to_validate'
    batch_id = fields.Many2one('batch.attendance.sheet', string="batch_id")
    employee_id = fields.Many2one('hr.employee', string='Employee')
    sheet_ids_to_validate = fields.Many2many('attendance.sheet', string='Employees Attendance Sheet',
                                             ondelete='cascade')


class batch_to_approve_attendance_sheet(models.Model):
    _name = 'attendance.sheet.to_approve'
    batch_id = fields.Many2one('batch.attendance.sheet', string="batch_id")
    employee_id = fields.Many2one('hr.employee', string='Employee')
    sheet_ids_to_approve = fields.Many2many('attendance.sheet', string='Employees Attendance Sheet', ondelete='cascade')


class batch_approved_attendance_sheet(models.Model):
    _name = 'attendance.sheet.approved'
    batch_id = fields.Many2one('batch.attendance.sheet', string="batch_id")
    employee_id = fields.Many2one('hr.employee', string='Employee')
    sheet_ids_approved = fields.Many2many('attendance.sheet', string='Employees Attendance Sheet', ondelete='cascade')


class HrLeaveAllocation(models.Model):
    _inherit = 'hr.leave.allocation'

    att_sheet_id = fields.Many2one('attendance.sheet')
    att_sheet_deduct = fields.Float()
