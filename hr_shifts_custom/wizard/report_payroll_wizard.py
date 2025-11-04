# from odoo import SUPERUSER_ID
from odoo import models, fields, api
# from odoo.exceptions import except_orm, Warning, RedirectWarning
import logging
class payroll_accumlate_report_wizard(models.TransientModel):
    _name = "payroll.accumlate.report"
    from_date = fields.Date("From Date")
    to_date = fields.Date("To Date")
    salary_rule = fields.Many2many('hr.salary.rule',string="Salary Rule")
    
    # @api.model
    # def default_get(self, fields):
    #     res = super(attendance_sheet_line_change, self).default_get(fields)
    #     atts_line_id = self.env[self._context['active_model']].browse(self._context['active_id'])
    #     if 'overtime' in fields and 'overtime' not in res:
    #         res['overtime'] = atts_line_id.overtime
    #         res['late_in'] = atts_line_id.late_in
    #         res['diff_time'] = atts_line_id.diff_time
    #         res['att_line_id'] = atts_line_id.id
    #     return res
    def get_lines(self):
        emp_dict={}
        payslips=self.env['hr.payslip'].search([('date_from','>=',self.from_date),('date_to','<=',self.to_date),('state','=','done')])
        for payslip in payslips:
            if payslip.employee_id.id not in emp_dict:
                emp_dict[payslip.employee_id.id]={
                        'name':payslip.employee_id.name,
                        'total':0,
                        }
            for line in payslip.line_ids:
                if line.salary_rule_id.id in self.salary_rule.ids:
                    t_val=line.total
                    if payslip.employee_id.id in emp_dict:
                        t_val+=emp_dict[payslip.employee_id.id]['total']

                    emp_dict[payslip.employee_id.id]={
                    'name':payslip.employee_id.name,
                    'total':t_val,
                    }               

        logging.info(">>>>>>>>data======"+str(emp_dict))
        return emp_dict
    def print_report(self):

        data = {
            'model_id': self.id,
            'model': 'hr.payslip',
             'from_date':self.from_date,
             'to_date':self.to_date,
             'salary_rule': [x.name for x in self.salary_rule],
             'lines':self.get_lines()
        }
        return self.env.ref('hr_shifts_custom.print_accumlate_payroll').report_action(self,data=data)
