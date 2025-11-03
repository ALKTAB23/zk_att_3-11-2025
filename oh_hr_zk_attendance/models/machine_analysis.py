# -*- coding: utf-8 -*-

from odoo import tools
from odoo import models, fields, api, _


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    device_id = fields.Char(string='Biometric Device ID', help="Give the biometric device id")
    device_ids = fields.One2many('hr.employee.devices_ids','emp_id',string='Biometric Devices ID', help="Give the biometric device ids of employee")

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
    machine_ip=fields.Many2one('zk.machine',string='Machine IP')
    is_process=fields.Boolean('is_process',default=False)

    @api.onchange('check_in')
    def _get_date_default(self):
        self.att_date=self.check_in.date()

class ReportZkDevice(models.Model):
    _name = 'zk.report.daily.attendance'
    _auto = False
    _order = 'punching_day desc'

    name = fields.Many2one('hr.employee', string='Employee', help="Employee")
    punching_day = fields.Date(string='Date', help="Punching Date")
    address_id = fields.Many2one('res.partner', string='Working Address')
    attendance_typee = fields.Char(string='Category')
    punch_type = fields.Selection([('0', 'Check In'),
                                   ('1', 'Check Out'),
                                   ('2', 'Break Out'),
                                   ('3', 'Break In'),
                                   ('4', 'Overtime In'),
                                   ('5', 'Overtime Out'),
                                   ('255', 'Check In')], string='Punching Type', help="Select the punch type")
    punching_time = fields.Datetime(string='Punching Time', help="Punching Time")
    is_process=fields.Boolean('Is Process',default=False)
    def init(self):
        tools.drop_view_if_exists(self._cr, 'zk_report_daily_attendance')
        query = """
            create or replace view zk_report_daily_attendance as (
                select
                    min(z.id) as id,
                    z.employee_id as name,
                    z.punching_day as punching_day,
                    z.address_id as address_id,
                    z.attendance_typee as attendance_typee,
                    z.punching_time as punching_time,
                    z.punch_type as punch_type
                from zk_machine_attendance z
                    join hr_employee e on (z.employee_id=e.id)
                GROUP BY
                    z.employee_id,
                    z.punching_day,
                    z.address_id,
                    z.attendance_typee,
                    z.punch_type,
                    z.punching_time
            )
        """
        self._cr.execute(query)


