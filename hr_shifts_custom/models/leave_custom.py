from odoo import fields, models, api
from pytz import timezone, UTC
import logging
from datetime import datetime, date, timedelta
from odoo.exceptions import ValidationError


class HolidaysRequestCustom(models.Model):
    _inherit = "hr.leave"

    def date_range_list(self, start_date, end_date):
        # Return list of datetime.date objects between start_date and end_date (inclusive).
        date_list = []
        curr_date = start_date
        # compare as date to exact match with date not time
        while curr_date.date() <= end_date.date():
            date_list.append(curr_date)
            curr_date += timedelta(days=1)
        return date_list

    @api.depends('number_of_days')
    def _compute_number_of_hours_display(self):
        for holiday in self:
            calendar = holiday._get_calendar()
            if holiday.date_from and holiday.date_to:
                # Take attendances into account, in case the leave validated
                # Otherwise, this will result into number_of_hours = 0
                # and number_of_hours_display = 0 or (#day * calendar.hours_per_day),
                # which could be wrong if the employee doesn't work the same number
                # hours each day
                number_of_hours = \
                holiday._get_number_of_days(holiday.date_from, holiday.date_to, holiday.employee_id.id)['hours']
                holiday.number_of_hours_display = number_of_hours
            else:
                holiday.number_of_hours_display = 0

    # Customize to cacluate based on schedule to calculte the correct days and hours or half hour of work schedule
    def _get_number_of_days(self, date_from, date_to, employee_id):
        """ Returns a float equals to the timedelta between two dates given as string."""
        days = 0.0
        hours = 0.0
        if employee_id:
            self.validate_leave_end_date(employee_id, date_to)
            attend_date_to = datetime(self.request_date_to.year, self.request_date_to.month, self.request_date_to.day)
            for day in self.date_range_list(date_from, attend_date_to):
                attend_date_now = datetime(day.year, day.month, day.day)
                match_shift_computed = self.env['zk.machine'].get_match_shift(str(attend_date_now), employee_id)
                if match_shift_computed:
                    if match_shift_computed.day_period != 'rest':
                        if self.request_unit_half:
                            hours = match_shift_computed.schedule_id.hours_per_day / 2
                        else:
                            if self.request_unit_hours:
                                hours = float(self.request_hour_to) - float(self.request_hour_from)
                            else:
                                hours += match_shift_computed.schedule_id.hours_per_day
                        days = days + 1 if not self.request_unit_half else 0.5
        return {'days': days, 'hours': hours}

    # Custom function to calculate the type of schedule f it is (rotation daily) change end date to include rest shift days within leave request and else to exclude with other types
    def validate_leave_end_date(self, employee_id, end_date):
        hours = 0
        days = 0
        attend_date_end_now = datetime(end_date.year, end_date.month, end_date.day)
        match_shift_computed = self.env['zk.machine'].get_match_shift(str(attend_date_end_now), employee_id)
        if match_shift_computed:
            if match_shift_computed.schedule_id.work_schedule_type == 'rotation':
                if match_shift_computed.schedule_id.recurring_sequence == 'daily':
                    curr_date = end_date
                    curr_date += timedelta(days=1)
                    while True:
                        date_cur = datetime(curr_date.year, curr_date.month, curr_date.day)
                        match_shift = self.env['zk.machine'].get_match_shift(str(date_cur), employee_id)
                        if match_shift.day_period != 'rest':
                            break
                        else:
                            leave_e_date = curr_date
                            hours += match_shift.schedule_id.hours_per_day
                            days = days + 1 if not self.request_unit_half else 0.5
                            # to update readonly variable after update context
                            self = self.with_context({
                                'leave_skip_state_check': True,
                            })
                            self.request_date_to = curr_date.date()
                            curr_date += timedelta(days=1)

    def action_validate(self):
        current_employee = self.env.user.employee_id
        super(HolidaysRequestCustom, self).action_validate()

        # Custom Update to get number of days and hours from Work Schedule rather than standard Calendar
        if self.request_date_from:
            if self.request_unit_half or self.request_unit_hours:
                self._get_number_of_days(
                    datetime(self.request_date_from.year, self.request_date_from.month, self.request_date_from.day),
                    datetime(self.request_date_from.year, self.request_date_from.month, self.request_date_from.day),
                    current_employee.id)
            else:
                self._get_number_of_days(
                    datetime(self.request_date_from.year, self.request_date_from.month, self.request_date_from.day),
                    datetime(self.request_date_to.year, self.request_date_to.month, self.request_date_to.day),
                    current_employee.id)
        return True


class HrLeaveType(models.Model):
    _inherit = "hr.leave.type"

    attendance_deduct = fields.Boolean(string='Deduct From Attendance', default=False)
