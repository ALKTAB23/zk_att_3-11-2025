from odoo import fields, models,api,_
from odoo.exceptions import Warning as UserError
import logging
class HR_shift_generate_Custom(models.Model):
    _inherit = 'hr.shift.generate'
    category_ids = fields.Many2many('hr.employee.category', string="Tags", help="Employee Tags")
    hr_department = fields.Many2many('hr.department', string="Department", help="Department")
    shift_schedule_id=fields.Many2one('resource.calendar',required=True,string="Shift")
    employee_ids = fields.Many2many('hr.employee', string="Employees", help="Employees")
    end_date = fields.Date(string="End Date", required=False, help="End date")
    
    def action_schedule_shift(self):
        """Create mass schedule for all departments based on the shift scheduled in corresponding employee's contract"""
        dep_ids=self.env['hr.department'].search([('id', 'child_of', self.hr_department.ids)])

        if self.hr_department and not self.category_ids:

            for contract in self.env['hr.contract'].search([('department_id', 'in', dep_ids.ids),('state','=','open')]):
                # check to get the employee contract if he have multiple contracts
                if contract.type_id.is_primary:
                    start_date = self.start_date
                    end_date = self.end_date or False
                    shift_ids = [(0, 0, {
                        'hr_shift': self.shift_schedule_id.id,
                        'start_date': start_date,
                        'end_date': end_date
                    })]
                    contract.shift_schedule = shift_ids
        else:
            # my customized code for employee tags 
            if self.category_ids and self.hr_department:
                contracts=[]
                employees=self.env['hr.employee'].search([('category_ids','in',self.category_ids.ids)])

                contracts=self.env['hr.contract'].search([('employee_id','in',employees.ids),('department_id', 'in', dep_ids.ids),('state','=','open')])
                for contract in contracts:
                    # check to get the employee contract if he have multiple contracts
                    if contract.type_id.is_primary:
                        start_date = self.start_date
                        end_date = self.end_date
                        shift_ids = [(0, 0, {
                                    'hr_shift': self.shift_schedule_id.id,
                                    'start_date': start_date,
                                    'end_date': end_date or False
                        })]

                        contract.shift_schedule = shift_ids
            else:
                if self.category_ids:
                    for employee in self.env['hr.employee'].search([('category_ids','in',self.category_ids.ids)]):
                        contract=self.env['hr.contract'].get_employee_contract(employee)
                        if contract:
                            if contract.state=='open':
                                start_date = self.start_date
                                end_date = self.end_date
                                shift_ids = [(0, 0, {
                                        'hr_shift': self.shift_schedule_id.id,
                                        'start_date': start_date,
                                        'end_date': end_date or False
                                })]
                                
                                contract.shift_schedule = shift_ids
                else:
                    if self.employee_ids:
                        for contract in self.env['hr.contract'].search([('employee_id','in',self.employee_ids.ids),('state','=','open')]):
                            # check to get the employee contract if he have multiple contracts
                            if contract.type_id.is_primary:
                                if contract.department_id:
                                    start_date = self.start_date
                                    end_date = self.end_date
                                    shift_ids = [(0, 0, {
                                            'hr_shift': self.shift_schedule_id.id,
                                            'start_date': start_date,
                                            'end_date': end_date or False
                                    })]
                                    contract.shift_schedule = shift_ids
                    else:
                        for contract in self.env['hr.contract'].search([('state','=','open')]):
                            # check to get the employee contract if he have multiple contracts
                            if contract.type_id.is_primary:
                                if contract.shift_schedule and contract.department_id:

                                    start_date = self.start_date
                                    end_date = self.end_date
                                    shift_ids = [(0, 0, {
                                            'hr_shift': self.shift_schedule_id.id,
                                            'start_date': start_date,
                                            'end_date': end_date or False
                                    })]
                                    contract.shift_schedule = shift_ids