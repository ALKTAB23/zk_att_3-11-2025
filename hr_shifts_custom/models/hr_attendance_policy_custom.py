from odoo import fields, models,api,_

class HrAttendancePolicy_Custom(models.Model):
    _inherit = 'hr.attendance.policy'
    permit_check_in=fields.Float('Permit Check In')
    permit_check_out=fields.Float('Permit Check Out')
    forget_rule_id=fields.Many2one('hr.forget.rule',string='Forget Register Policy',required=True)

class HrOvertimeRule_custom(models.Model):
    _inherit = 'hr.overtime.rule'

    type = [
        ('weekend', 'Week End'),
        ('workday', 'Working Day'),
        ('ph', 'Public Holiday')
    ]
    type = fields.Selection(selection=type, string="Type", default='workday')

class HrPolicy_overtimeLine_custom(models.Model):
    _inherit = 'hr.policy.overtime.line'
    type = [
        ('weekend', 'Week End'),
        ('workday', 'Working Day'),
        ('ph', 'Public Holiday')
    ]
    type = fields.Selection(selection=type, string="Type", default='workday')
    
class HrLateRule_custom(models.Model):
    _inherit = 'hr.late.rule.line'
    types = [
        ('fix', 'Fixed'),
        ('rate', 'Rate'),
        ('rate_fix', 'Rate and Fixed')
    ]
    type = fields.Selection(string="Type", selection=types, required=True, )
    time_limit=fields.Float(string="To Time",required=True)
    time = fields.Float('From Time', required=True)
    amount = fields.Float('Hours')
    times = [
        ('1', 'First Time'),
        ('2', 'Second Time'),
        ('3', 'Third Time'),
        ('4', 'Fourth Time'),
        ('5', 'Fifth Time'),

    ]
    counter = fields.Selection(string="Times", selection=times, required=True, )

class HrDiffRule_custom(models.Model):
    _inherit = 'hr.diff.rule.line'
    types = [
        ('fix', 'Fixed'),
        ('rate', 'Rate'),
        ('rate_fix', 'Rate and Fixed')
    ]
    type = fields.Selection(string="Type", selection=types, required=True, )
    time_limit=fields.Float(string="To Time",required=True)
    amount = fields.Float('Hours')
    time = fields.Float('From Time', required=True)
    times = [
        ('1', 'First Time'),
        ('2', 'Second Time'),
        ('3', 'Third Time'),
        ('4', 'Fourth Time'),
        ('5', 'Fifth Time'),
    ]
    counter = fields.Selection(string="Times", selection=times, required=True, )
class HrForegetRule(models.Model):
    _name = 'hr.forget.rule'
    _description = 'Forget Register Rules'

    name = fields.Char(string='name', required=True)
    line_ids = fields.One2many(comodel_name='hr.forget.rule.line',
                               inverse_name='forget_id',
                               string='Forget Register Rules')

class HrForgetAttendance_RuleLine(models.Model):
    _name = 'hr.forget.rule.line'
    _description = 'Forget Register Rule Lines'
    times = [
        ('1', 'First Time'),
        ('2', 'Second Time'),
        ('3', 'Third Time'),
        ('4', 'Fourth Time'),
        ('5', 'Fifth Time'),

    ]
    forget_id = fields.Many2one(comodel_name='hr.forget.rule', string='name')
    rate = fields.Float(string='Rate', required=True)
    counter = fields.Selection(string="Times", selection=times, required=True, )