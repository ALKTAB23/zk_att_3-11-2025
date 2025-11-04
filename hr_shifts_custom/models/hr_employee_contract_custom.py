from odoo import fields, models,api,_
import time,os
from datetime import datetime, timedelta
from odoo.exceptions import Warning as UserError
import logging
_logger = logging.getLogger(__name__)
import pytz
# os.environ['TZ'] = 'Asia/Riyadh'
class HR_Contract_types_Custom(models.Model):
    _inherit = 'hr.contract.type'
    is_primary=fields.Boolean('Is Primary?',default=False)
    
class HR_Contract_schedule_Custom(models.Model):
    _inherit = 'hr.contract'
    shift_schedule2 = fields.One2many('contract.hr.shift.schedule', 'rel_hr_schedule', string="Shift Schedule", readonly=True, help="Shift schedule", ondelete="cascade")
    recurring_sequence=fields.Selection(string='Recurring Sequence', related='working_hours.recurring_sequence')
    resource_calendar_id = fields.Many2one(
        'resource.calendar', 'Working Schedule', compute='_compute_employee_contract', store=True, required=False, readonly=False,
        default=lambda self: self.env.company.resource_calendar_id.id, copy=False, index=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    hours_per_day = fields.Float("Current AVG Hour per Day", readonly=True, force_store=True, compute='_compute_hours_per_day_avg',
                                 help="Average hours per day a resource is supposed to work with this calendar.")
    manual_avg=fields.Boolean('Fix AVG?',default=False)
    fix_hours_per_day = fields.Float('Fix AVG Hours Per Day')
    
    
    def get_employee_contract(self,emp):
        emp_recs=self.env['hr.contract'].search([('employee_id','=',emp.id),('state','=','open')])
        for contract in emp_recs:
            if contract.type_id.is_primary:
                return contract
        return False
    def get_schedule(self,contract_id,current_date):
        schedules=contract_id.shift_schedule
        match_schedules=schedules.search([('start_date','<=',str(current_date)),('active','=',True),('rel_hr_schedule','=',contract_id[0].id)])
        active_schedule_id=False
        sft_start_date=False
        for sc in match_schedules:
            if sc.end_date:
                sc_end_date=datetime(sc.end_date.year,sc.end_date.month,sc.end_date.day)
                if current_date <= sc_end_date.date():
                    active_schedule_id=sc.hr_shift
            else:
                active_schedule_id=sc.hr_shift
        return active_schedule_id
    @api.depends('shift_schedule')
    def _compute_hours_per_day_avg(self):
        shift=False
        if self.manual_avg==False:
            for sh in self.shift_schedule:
                shift=sh
            if shift:
                self.hours_per_day=shift.hr_shift.hours_per_day
            else:
                self.hours_per_day=0
        else:
            self.hours_per_day=self.fix_hours_per_day
    
    @api.model
    def create(self, vals):
        # hours=self._compute_hours_per_day_avg()
        # vals['hours_per_day']=hours
        return super(HR_Contract_schedule_Custom, self).create(vals)
    def write(self, vals):
        # hours=self._compute_hours_per_day_avg()
        # vals['hours_per_day']=hours
        res = super(HR_Contract_schedule_Custom, self).write(vals)
        if vals.get('state') == 'open':
            self._assign_open_contract()
        if vals.get('state') == 'close':
            for contract in self.filtered(lambda c: not c.date_end):
                contract.date_end = max(date.today(), contract.date_start)
        
        calendar = vals.get('resource_calendar_id')
        if calendar:
            self.filtered(lambda c: c.state == 'open' or (c.state == 'draft' and c.kanban_state == 'done')).mapped('employee_id').write({'resource_calendar_id': calendar})

        if 'state' in vals and 'kanban_state' not in vals:
            self.write({'kanban_state': 'normal'})

        return res
class HR_Shift_schedule_Custom(models.Model):
    _inherit = 'hr.shift.schedule'
    
    name = fields.Char(required=False)
    day_period = fields.Selection([('morning', 'Morning'), ('afternoon', 'Afternoon'),('rest','Rest'),('weekend','Weekend')], required=True, default='morning')
    end_date = fields.Date(string="Date To", required=False, help="Ending date for the shift")
    week_type = fields.Selection([
        ('0', ''),
        ('1', 'First Week'),
        ('1', 'Second Week'),
        ('1', 'Third Week'),
        ('1', 'Fourth Week')
        ], 'Week', default='0')
    dayofweek = fields.Selection([
        ('0', ''),
        ('1', 'Saterday'),
        ('2', 'Sunday'),
        ('3', 'Monday'),
        ('4', 'Tuesday'),
        ('5', 'Wednesday'),
        ('6', 'Thursday'),
        ('7', 'Friday')
        ], 'Day of Week', index=True, default='0')
    hour_from = fields.Float(string='From Time', required=False, index=True,
        help="Start and End time of working.\n"
             "A specific value of 24:00 is interpreted as 23:59:59.999999.")
    hour_to = fields.Float(string='To Time', required=False)
    active = fields.Selection([
        ('True', 'True'),
        ('False', 'False'),
        ], string='Active?', default='True')
    @api.onchange('start_date', 'end_date')
    def get_department(self):
        """Adding domain to  the hr_shift field"""
        pass

class HR_ContractShift_schedule_Custom(models.Model):
    _name='contract.hr.shift.schedule'
    _inherit = 'hr.shift.schedule'

    name = fields.Char(required=False)
    request_id=fields.Many2one('resource.calendar.shift.changeshift','Request ID')
    hr_shift=fields.Many2one('shift_data', string='Shift', required=True)
    hour_from = fields.Float(string='Work from', readonly=True, related='hr_shift.hour_from',
        help="Start and End time of working.\n"
             "A specific value of 24:00 is interpreted as 23:59:59.999999.")
    hour_to = fields.Float(string='Work to',readonly=True ,related='hr_shift.hour_to',)
    day_period = fields.Selection([('morning', 'Morning'), ('afternoon', 'Afternoon'),('rest','Rest'),('weekend','Weekend')], required=True, default='morning', readonly=True,related='hr_shift.day_period')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('manager_approve', 'Direct Manager Approval'),
        ('approved', 'Approved'),
        ('reject', 'Rejected'),
        ('canceled','Canceled')
        ], string='State', required=True, default='draft')
