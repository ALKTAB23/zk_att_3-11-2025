from odoo import fields, models,api,_
import time,os
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from odoo.exceptions import Warning as UserError
import logging
_logger = logging.getLogger(__name__)
import pytz
class resource_calendar_attendance_custom(models.Model):
    _name = 'resource.calendar.shift.changeshift'
    _rec_name = 'request_type' 

    employee_id=fields.Many2one('hr.employee',string='Employee',required=True)
    shift_date=fields.Date('Shift Date',required=True)
    current_shift=fields.Many2one('shift_data', string="Current Shifts Schedule",readonly=True, help="Current Shifts",store=True,)
    c_hour_from=fields.Float(string='Work from', readonly=True, index=True,
        help="Start and End time of working.\n"
             "A specific value of 24:00 is interpreted as 23:59:59.999999.", related='current_shift.hour_from',store=True, force_store=True)
    c_hour_to=fields.Float(string='Work to', readonly=True,related='current_shift.hour_to',store=True, force_store=True)
    newshift_name=fields.Many2one('shift_data',string='New Shift',required=True)
    new_day_period = fields.Selection([('morning', 'Morning'), ('afternoon', 'Afternoon'),('rest','Rest'),('weekend','Weekend')], required=True, default='morning')

    new_hour_from = fields.Float(string='Work from', readonly=True, index=True,
        help="Start and End time of working.\n"
             "A specific value of 24:00 is interpreted as 23:59:59.999999.", related='newshift_name.hour_from')
    new_hour_to = fields.Float(string='Work to', readonly=True,related='newshift_name.hour_to')
    current_shift_rec=fields.Many2one('schedule_attendances',string='current shift record')
    request_type = fields.Selection([
        ('change', 'Change Shift'),
        ('add_workday', 'Add New Shift In Holiday'),
        # ('add_multi', 'Add New Shift In Workday'),
        ('compensate_shift', 'Compensate Shift'),
        ('petition_request', '؛Petition request')
        ], 'Request Type', required=True, default='change')
    request_date=fields.Date('Request Date',default=fields.datetime.now(),readonly=True)
    reasons=fields.Text(string="Reasons",required=True)
    approve_notes=fields.Text(string="Approve Notes", readonly=True)
    approve_date=fields.Date('Approve Date',readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('manager_approve', 'Direct Manager Approval'),
        ('approved', 'Approved'),
        ('reject', 'Rejected'),
        ('canceled','Canceled')
        ], string='State', required=True, default='draft')
    def days_between(self,d1, d2):
        return abs((d2 - d1).days)
    
    def get_match_shift(self,current_time, current_employee):
        emp_rec=self.env['hr.contract'].search([('employee_id','=',current_employee),('state','=','open')],limit=1)
        attend_date_now=datetime.strptime(current_time,'%Y-%m-%d')
        attend_date_now=datetime(attend_date_now.year,attend_date_now.month,attend_date_now.day)
        diff_no=0
        shift_index=0
        # current_emp_date=datetime(current_emp_date.year,current_emp_date.month,current_emp_date.day).strftime('%Y-%m-%d')
        # current_emp_date=datetime.strptime(current_emp_date,'%Y-%m-%d')
        if emp_rec:
            schedules=emp_rec[0].shift_schedule
            match_schedules=schedules.search([('start_date','<=',str(attend_date_now)),('active','=',True),('rel_hr_schedule','=',emp_rec[0].id)])
            active_schedule_id=False
            sft_start_date=False
            for sc in match_schedules:
                if sc.end_date:
                    sc_end_date=datetime(sc.end_date.year,sc.end_date.month,sc.end_date.day)
                    if attend_date_now.date() <= sc_end_date.date():
                        sft_start_date=sc.start_date
                        diff_no=self.days_between(sft_start_date,attend_date_now.date())
                        active_schedule_id=sc.hr_shift
                else:
                    sft_start_date=sc.start_date
                    diff_no=self.days_between(sft_start_date,attend_date_now.date())
                    active_schedule_id=sc.hr_shift
            
            shift_index=diff_no
            if active_schedule_id:
                shifts_len=len(active_schedule_id.shifts_config_ids)
                shift_index=diff_no
                for n in range(diff_no):
                    if shift_index<shifts_len:
                        break
                    shift_index=shift_index-shifts_len
            match_shift=False
            if active_schedule_id:
                # if diff_no<shifts_len:
                if active_schedule_id.recurring_sequence=='weekly':
                    day=attend_date_now.weekday()
                    for r in active_schedule_id.shifts_config_ids.sorted(lambda o: o.sequence):
                        if str(r.dayofweek)==str(day) and r.week_type==active_schedule_id.shifts_config_ids.sorted(lambda o: o.sequence)[shift_index].week_type:
                            # dd=calendar.weekday(attend_date_now.date().year,attend_date_now.date().month,attend_date_now.date().day)

                            match_shift=r
                            break                    
                else:#daily
                    match_shift=active_schedule_id.shifts_config_ids.sorted(lambda o: o.sequence)[shift_index]

            return match_shift
    def getcurrentshift(self):        
        match_shift=self.get_match_shift(str(self.shift_date), self.employee_id.id)
        if match_shift:
            self.current_shift_rec=match_shift.id
            self.current_shift=match_shift.hr_shift.id
        return True

    def request_direct_manager_approve(self):
        requests_rec=self.env['resource.calendar.shift.changeshift'].search([('employee_id','=',self.employee_id.id),
            ('request_type','=',self.request_type),
            ('shift_date','=',self.shift_date),('state','=','approved')])
        if requests_rec:
            raise ValidationError(_("You can't request more than one request in day!"))
        self.state='manager_approve'
        return True
    
    def request_hr_manager_approve(self):
        is_approve=False
        if self.request_type=='add_workday':
            if self.current_shift.day_period=='rest' or self.current_shift.day_period=='weekend':
                is_approve=True
            else:
                pass
        else:
            if self.request_type=='change':
                is_approve=True
            else:
                if self.request_type=='compensate_shift':
                    is_approve=True
        if is_approve:
            self.approve_date=fields.datetime.now()
            new_shift_ids = [(0, 0, {
                        'hr_shift': self.newshift_name.id,
                        'day_period': self.new_day_period,
                        'hour_from': self.new_hour_from,
                        'hour_to': self.new_hour_to,
                        'start_date':self.shift_date,
                        'end_date':self.shift_date,
                        'request_id':self.id,                        
                        'state':'approved'
                        })]
            self.employee_id.contract_id.shift_schedule2=new_shift_ids
            self.state='approved'
        return True

    def request_reject(self):
        self.state='reject'
        return True
    
    def request_cancel(self):
        emp_rec=self.env['contract.hr.shift.schedule'].search([('request_id','=',self.id)])
        if emp_rec:
            emp_rec[0].state='canceled'
        self.state='canceled'
        return True