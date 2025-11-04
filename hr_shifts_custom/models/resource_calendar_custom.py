# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models,api,_
import time,os
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)
import pytz
from odoo.tools.float_utils import float_round
# os.environ['TZ'] = 'Asia/Riyadh'

import calendar
class HrAttendance(models.Model):
    _inherit = 'hr.attendance'
    
    check_in = fields.Datetime(string="Check In", default=fields.Datetime.now, required=False)
    match_shift=fields.Many2one('shift_data',string='Match Shift')
    att_shift_rec=fields.Many2one('schedule_attendances',string='Shift Record',order="sequence")
    expected_check_in = fields.Float(string="Expected Check In")
    expected_check_out = fields.Float(string="Expected Check Out")
    act_over_time = fields.Float(string='Over Time', readonly=True)
    act_diff_time = fields.Float(string='Early Checkout', readonly=True)
    act_delay_time = fields.Float(string='Delay Time', readonly=True)
    overtime_limit = fields.Float(string='Allowed Overtime', readonly=True)
    leave_hours=fields.Float(string='Leave Hours', readonly=True)
    linked_request=fields.Many2one('resource.calendar.shift.changeshift',string='Linked Request')
    sheet_id=fields.Many2one('attendance.sheet',string="Linked Sheet")    
    def write(self, vals):
        if 'match_shift' in vals:
            shi=self.env['shift_data'].browse(vals['match_shift'])
            
            if self.check_out:
                pass
                # delay,diff,overtime=self.env['zk.machine'].calculate_delay_diff_overtime(self.att_shift_rec,self.check_in,self.check_out,shi)
                # vals['act_delay_time']=delay
                # vals['act_diff_time']=diff
                # vals['act_over_time']=overtime
                # vals['expected_check_in']=shi.hour_from
                # vals['expected_check_out']=shi.hour_to
        return super(HrAttendance, self).write(vals)

class Resource_calendar_custom(models.Model):
    _inherit = 'resource.calendar'
    
    def days_between(self,d1, d2):
        return abs((d2 - d1).days)

    def write(self, vals):
        # self._compute_hours_per_day_avg()
        return super(Resource_calendar_custom, self).write(vals)

    shifts_config_ids = fields.One2many('schedule_attendances', 'schedule_id', string='Shifts Configuration', ondelete='cascade',order="sequence")
    recurring_sequence=fields.Selection([('daily','Daily'),('weekly','Weekly')],string="Recurrent",default='daily')
    
    recurring_number=fields.Integer('Recurrent Number', )
    dayofweek = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
        ], 'Day of Week', required=True, index=True, default='0')
    calc_method=fields.Selection([('fix','Fixed')],string='Calculation method',default='fix')
    default_shift=fields.Many2one('shift_data', string='Default Shift', required=True)
    # default_rest=fields.Many2one('shift_data', string='Default Rest Shift', domain=[('day_period','=','rest')])
    default_policy=fields.Many2one('hr.attendance.policy', string='Default Shift Policy',required=True)
    append_to=fields.Boolean('Generate and Append?',default=False)
    is_24h=fields.Boolean('Is 24H?',default=False)
    default_week=fields.Selection([
        ('0', ''),
        ('1', '1st Week'),
        ('2', 'Snd Week'),
        ('3', '3rd Week'),
        ('4', '4th Week'),
        ('5', '5th Week'),
        ('6', '6th Week')
        ], 'Default Week', default='0',)
    manual_avg=fields.Boolean('Fix AVG?',default=False)
    fix_hours_per_day = fields.Float('AVG Hour per Day')
    hours_per_day = fields.Float("AVG Hour per Day", compute='_compute_hours_per_day_avg', force_store=True,
                                 help="Average hours per day a resource is supposed to work with this calendar.",readonly=True)
    work_schedule_type=fields.Selection([('normal','Normal Schedule'),('rotation','Rotation Schedule')],string="Schedule Type",default='normal')

    
    @api.depends('shifts_config_ids')
    def _compute_hours_per_day_avg(self):
        hour_count = 0.0
        c=0
        for rec in self:
            if rec.manual_avg==False:
                for attendance in rec.shifts_config_ids.sorted(lambda o: o.sequence):
                    if attendance.day_period!='rest' and attendance.day_period!='weekend':
                        hour_count += self.env['zk.machine'].subtract_two_times_24h(attendance.hour_to,attendance.hour_from)
                    else:
                        c+=1
                number_of_days = len(rec.shifts_config_ids)-c
                if number_of_days>0:
                    rec.hours_per_day=float_round(hour_count/float(number_of_days), precision_digits=2)
                else:
                    rec.hours_per_day=0
            else:
                rec.hours_per_day=rec.fix_hours_per_day
    
    def update_shifts(self):
        for rec in self.shifts_config_ids.sorted(lambda o: o.sequence):
            rec.hour_from=rec.hr_shift.hour_from
            rec.hour_to=rec.hr_shift.hour_to
            

        self._compute_hours_per_day_avg()
    def generate_shifts(self):
        result = [] # # # # # #updated code now its working
        if self.work_schedule_type=='rotation':
            if self.recurring_sequence=='weekly':
                if self.recurring_number>6:
                    raise ValidationError(_("The Recurrent must be 6 times or Less for weekly Recurrent!"))
            if self.append_to==False:
                for rec in self.shifts_config_ids:
                    rec.unlink()

            def_range=self.recurring_number
            count =1
            if self.recurring_sequence=='weekly':
                def_range=self.recurring_number*7
                if self.append_to:
                    last_week=self.shifts_config_ids.sorted(lambda o: o.sequence)[len(self.shifts_config_ids)-1].week_type
                    if last_week=='1':
                        count=8
                    else:
                        if last_week=='2':
                            count=15
                        else:
                            if last_week=='3':
                                count=22
                            else:
                                if last_week=='4':
                                    count=29
                                else:
                                    if last_week=='5':
                                        count=36
                                    else:
                                        raise ValidationError(_("The Weekly Recurrent must be 6 weeks or Less!"))
            
            gen_day=0
            for i in range(def_range):
                if self.default_shift and self.default_policy:
                    compute_week='0'
                    if self.recurring_sequence=='weekly':
                        if count>=1 and count <= 7:
                            compute_week='1'
                        else:
                            if count>=8 and count<=14:
                                compute_week='2'
                            else:
                                if count>=15 and count<=21:
                                    compute_week='3'
                                else:
                                    if count>=22 and count<=28:
                                        compute_week='4'
                                    else:
                                        if count>=29 and count<=35:
                                            compute_week='5'
                                        else:
                                            if count>=36 and count<=42:
                                                compute_week='6'
                    
                    shift_ids = [(0, 0, {
                            'hr_shift': self.default_shift.id,
                            'dayofweek': str(gen_day),
                            'week_type': compute_week,
                            'day_period': self.default_shift.day_period,
                            'hour_from': self.default_shift.hour_from,
                            'hour_to': self.default_shift.hour_to,
                            'att_policy_id': self.default_policy.id,
                    })]
                    self.shifts_config_ids=shift_ids
                    count=count+1
                    if gen_day==6:
                        gen_day=0
                    else:
                        gen_day=gen_day+1
        else:#work_schedule_type=='normal'
            def_range=7
            self.recurring_sequence='weekly'

            for rec in self.shifts_config_ids:
                rec.unlink()
            count =1
            gen_day=0
            for i in range(def_range):
                if self.default_shift and self.default_policy:
                    # if str(gen_day) == '4' or str(gen_day) == '5':
                    #     shift_ids = [(0, 0, {
                    #             'hr_shift': self.default_rest.id,
                    #             'dayofweek': str(gen_day),
                    #             'week_type': '1',
                    #             'day_period': self.default_rest.day_period,
                    #             'hour_from': self.default_rest.hour_from,
                    #             'hour_to': self.default_rest.hour_to,
                    #             'att_policy_id': self.default_policy.id,
                    #     })]
                    #     self.shifts_config_ids=shift_ids
                    # else:
                    shift_ids = [(0, 0, {
                            'hr_shift': self.default_shift.id,
                            'dayofweek': str(gen_day),
                            'week_type': '1',
                            'day_period': self.default_shift.day_period,
                            'hour_from': self.default_shift.hour_from,
                            'hour_to': self.default_shift.hour_to,
                            'att_policy_id': self.default_policy.id,
                    })]
                    self.shifts_config_ids=shift_ids
                    count=count+1
                    if gen_day==6:
                        gen_day=0
                    else:
                        gen_day=gen_day+1

class resource2_calendar_attendance_custom(models.Model):
    _name = 'schedule_attendances'
    
    def write(self, vals):
        self._check_overlap(vals,'write')
        return super(resource2_calendar_attendance_custom, self).write(vals)

    @api.model
    def create(self, vals):
        self._check_overlap(vals,'create')
        return super(resource2_calendar_attendance_custom, self).create(vals)

    schedule_id = fields.Many2one("resource.calendar", string="Resource's Calendar", ondelete='cascade')
    sequence = fields.Integer(help="Gives the sequence of this line when displaying the resource calendar.")
    hr_shift=fields.Many2one('shift_data',required=True)

    date_from = fields.Date(string='Starting Date')
    date_to = fields.Date(string='End Date')
    att_policy_id=fields.Many2one('hr.attendance.policy','Shift Policy', required=True)
    hour_from = fields.Float(string='Work from', readonly=True, related='hr_shift.hour_from',
        help="Start and End time of working.\n"
             "A specific value of 24:00 is interpreted as 23:59:59.999999.")

    hour_to = fields.Float(string='Work to',readonly=True ,related='hr_shift.hour_to',)
    dayofweek = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
        ], 'Day of Week', required=True, index=True, default='0')
    week_type = fields.Selection([
        ('0', ''),
        ('1', '1st Week'),
        ('2', 'Snd Week'),
        ('3', '3rd Week'),
        ('4', '4th Week'),
        ('5', '5th Week'),
        ('6', '6th Week')
        ], 'Week', default='0',)
    day_period = fields.Selection([('morning', 'Morning'), ('afternoon', 'Afternoon'),('rest','Rest'),('weekend','Weekend')], required=True, default='morning', readonly=True,related='hr_shift.day_period')


    def _check_overlap(self, vals,opr):
        obj_att=False
        obj=False
        check=False
        if opr=='write':
            obj_att=self.env['schedule_attendances'].browse(self.id)
            obj=self.env['resource.calendar'].browse(obj_att.schedule_id.id)
        else:
            obj=self.env['resource.calendar'].browse(vals['schedule_id'])
        if obj.recurring_sequence=='weekly':
            if opr=='create':
                weekt=False
                if 'week_type' in vals:
                    weekt=vals['week_type']
                dayof=False
                hour_fromv=False
                hour_tov=False
                if 'dayofweek' in vals:
                    dayof=vals['dayofweek']
                if 'day_period' in vals:
                    dayperiod=vals['day_period']
                shift_obj=self.env['shift_data'].browse(vals['hr_shift'])
                hour_fromv=shift_obj.hour_from
                hour_tov=shift_obj.hour_to
                check_exist_week_day=False
                check_exist_week_day = self.env['schedule_attendances'].search([('schedule_id', '=', vals['schedule_id']),
                                        ('week_type','=',weekt),
                                            ('dayofweek','=',dayof)])
                if check_exist_week_day:
                    check=True
            else:
                #write opr
                _logger.info("in write-------------------")
                weekt=False
                if 'week_type' in vals:
                    weekt=vals['week_type']
                else:
                    weekt=obj_att.week_type
                dayof=False
                hour_fromv=False
                hour_tov=False
                if 'dayofweek' in vals:
                    dayof=vals['dayofweek']
                else:
                    dayof=obj_att.dayofweek
                shiftid=False
                if 'hr_shift' in vals:
                    shiftid=vals['hr_shift']
                else:
                    shiftid=obj_att.hr_shift.id
                shift_obj=self.env['shift_data'].browse(shiftid)
                hour_fromv=shift_obj.hour_from
                hour_tov=shift_obj.hour_to

                check_exist_week_day = self.env['schedule_attendances'].search([('schedule_id', '=', obj_att.schedule_id.id),
                                        ('week_type','=',weekt),
                                            ('dayofweek','=',dayof)])
                if len(check_exist_week_day)>1:
                    check=True              
            if check:
                raise ValidationError(_('There is overlap of shift times or Duplicate!'))

        return True



class resource_shift_data_custom(models.Model):
    _name = 'shift_data'

    name = fields.Char(required=True)
    hour_from = fields.Float(string='Work from', required=True, index=True,
        help="Start and End time of working.\n"
             "A specific value of 24:00 is interpreted as 23:59:59.999999.")
    hour_to = fields.Float(string='Work to', required=True)
    day_period = fields.Selection([('morning', 'Morning'), ('afternoon', 'Afternoon'),('rest','Rest'),('weekend','Weekend')], required=True, default='morning')