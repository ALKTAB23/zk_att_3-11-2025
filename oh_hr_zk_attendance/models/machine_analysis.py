# -*- coding: utf-8 -*-

from odoo import tools
from odoo import models, fields, api, _


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    device_id = fields.Char(string='Biometric Device ID', help="Give the biometric device id")
    device_ids = fields.One2many('hr.employee.devices_ids','emp_id',string='Biometric Devices ID', help="Give the biometric device ids of employee")
    authorized_area_ids = fields.Many2many('zk.device.area', 'employee_area_rel', 'employee_id', 'area_id', 
                                           string='Authorized Areas',
                                           help='Areas where this employee is authorized to work. Employee can punch in any device within these areas.')

class HrEmployee_Devices(models.Model):
    _name = 'hr.employee.devices_ids'
    emp_id=fields.Many2one('hr.employee',string="Employee")
    machine_ip=fields.Many2one('zk.machine',required=True)
    device_id=fields.Char('Device ID',required=True)

class ZkMachine(models.Model):
    _name = 'zk.machine.attendance'
    _inherit = 'hr.attendance'

    @api.constrains('check_in', 'check_out', 'employee_id')
    def _check_validity(self):
        """overriding the __check_validity function for employee attendance."""
        pass

    device_id = fields.Char(string='Biometric Device ID', help="Biometric device id")
    punch_type = fields.Selection([('0', 'Check In'),
                                   ('1', 'Check Out'),
                                   ('2', 'Break Out'),
                                   ('3', 'Break In'),
                                   ('4', 'Overtime In'),
                                   ('5', 'Overtime Out'),
                                   ('255', 'Check In')],
                                  string='Punching Type')

    attendance_typee = fields.Char(string='Category')
    
    punching_time = fields.Datetime(string='Punching Time', help="Give the punching time")
    address_id = fields.Many2one('res.partner', string='Working Address', help="Address")

    punching_day = fields.Date(string='Date', help="Punching Date")
    machine_ip = fields.Many2one('zk.machine', string='Machine IP')
    area_id = fields.Many2one('zk.device.area', string='Attendance Area', 
                              related='machine_ip.area_id', store=True, readonly=True,
                              help='Area where this attendance was recorded. Automatically set from device area.')
    is_process = fields.Boolean('is_process', default=False)

    @api.onchange('check_in')
    def _get_date_default(self):
        self.att_date=self.check_in.date()
    
    @api.model
    def create(self, vals):
        """Validate employee is authorized in the zone before creating attendance"""
        record = super(ZkMachine, self).create(vals)
        
        # Check if employee is authorized in this area (if areas are configured)
        if record.area_id and record.employee_id:
            if record.employee_id.authorized_area_ids:
                if record.area_id not in record.employee_id.authorized_area_ids:
                    # Log warning but don't block - allow attendance but mark for review
                    import logging
                    _logger = logging.getLogger(__name__)
                    _logger.warning(
                        f"Employee {record.employee_id.name} (ID: {record.employee_id.id}) "
                        f"punched in Area '{record.area_id.name}' but is not authorized. "
                        f"Authorized areas: {', '.join(record.employee_id.authorized_area_ids.mapped('name'))}"
                    )
        
        return record

class ReportZkDevice(models.Model):
    _name = 'zk.report.daily.attendance'
    _auto = False
    _order = 'punching_day desc'

    name = fields.Many2one('hr.employee', string='Employee', help="Employee")
    punching_day = fields.Date(string='Date', help="Punching Date")
    address_id = fields.Many2one('res.partner', string='Working Address')
    area_id = fields.Many2one('zk.device.area', string='Area', help='Area where attendance was recorded')
    attendance_typee = fields.Char(string='Category')
    punch_type = fields.Selection([('0', 'Check In'),
                                   ('1', 'Check Out'),
                                   ('2', 'Break Out'),
                                   ('3', 'Break In'),
                                   ('4', 'Overtime In'),
                                   ('5', 'Overtime Out'),
                                   ('255', 'Check In')], string='Punching Type', help="Select the punch type")
    punching_time = fields.Datetime(string='Punching Time', help="Punching Time")
    is_process = fields.Boolean('Is Process', default=False)
    act_delay_time = fields.Float('Delay Time')
    act_diff_time = fields.Float('Diff Time')
    act_over_time = fields.Float('Overtime')
    
    def init(self):
        tools.drop_view_if_exists(self._cr, 'zk_report_daily_attendance')
        query = """
            create or replace view zk_report_daily_attendance as (
                select
                    min(z.id) as id,
                    z.employee_id as name,
                    z.punching_day as punching_day,
                    z.address_id as address_id,
                    z.area_id as area_id,
                    z.attendance_typee as attendance_typee,
                    z.punching_time as punching_time,
                    z.punch_type as punch_type,
                    max(z.act_delay_time) as act_delay_time,
                    max(z.act_diff_time) as act_diff_time,
                    max(z.act_over_time) as act_over_time
                from zk_machine_attendance z
                    join hr_employee e on (z.employee_id=e.id)
                GROUP BY
                    z.employee_id,
                    z.punching_day,
                    z.address_id,
                    z.area_id,
                    z.attendance_typee,
                    z.punch_type,
                    z.punching_time
            )
        """
        self._cr.execute(query)


