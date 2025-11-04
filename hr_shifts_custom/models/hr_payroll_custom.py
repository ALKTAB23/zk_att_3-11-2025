# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models,api,_,tools
import babel
import math
from datetime import datetime, timedelta, time
import logging
_logger = logging.getLogger(__name__)
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_utils

class hr_payslip_inherit(models.Model):
    _inherit = 'hr.payslip'
    # YTI TODO To rename. This method is not really an onchange, as it is not in any view
    # employee_id and contract_id could be browse records
    def onchange_employee_id(self, date_from, date_to, employee_id=False, contract_id=False,sheet_id=False):

        # defaults
        res = {
            'value': {
                'line_ids': [],
                # delete old input lines
                'input_line_ids': [(2, x,) for x in self.input_line_ids.ids],
                # delete old worked days lines
                'worked_days_line_ids': [(2, x,) for x in self.worked_days_line_ids.ids],
                # 'details_by_salary_head':[], TODO put me back
                'name': '',
                'contract_id': False,
                'struct_id': False,
            }
        }
        if (not employee_id) or (not date_from) or (not date_to):
            return res
        ttyme = datetime.combine(fields.Date.from_string(date_from), time.min)
        employee = self.env['hr.employee'].browse(employee_id)
        locale = self.env.context.get('lang') or 'en_US'
        res['value'].update({
            'name': _('Salary Slip of %s for %s') % (
            employee.name, tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale))),
            'company_id': employee.company_id.id,
        })

        if not self.env.context.get('contract'):
            # fill with the first contract of the employee
            contract_ids = self.get_contract(employee, date_from, date_to)
        else:
            if contract_id:
                # set the list of contract for which the input have to be filled
                contract_ids = [contract_id]
            else:
                # if we don't give the contract, then the input to fill should be for all current contracts of the employee
                contract_ids = self.get_contract(employee, date_from, date_to)

        if not contract_ids:
            return res
        contract = self.env['hr.contract'].browse(contract_ids[0])
        res['value'].update({
            'contract_id': contract.id
        })
        struct = contract.struct_id
        if not struct:
            return res
        res['value'].update({
            'struct_id': struct.id,
        })
        # computation of the salary input
        contracts = self.env['hr.contract'].browse(contract_ids)
        # Custom modification >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        worked_days_line_ids = self.get_worked_day_lines(contracts, date_from, date_to, sheet_id)

        input_line_ids = self.get_inputs(contracts, date_from, date_to)
        # input_line_ids =super(hr_payslip_inherit, self).get_inputs(contracts, date_from, date_to)
        #Custom=0
        amount=0
        adv_salary = self.env['salary.advance'].search([('employee_id', '=', employee.id)])
        for adv_obj in adv_salary:
            current_date = date_from.month
            date = adv_obj.date
            existing_date = date.month
            if current_date == existing_date:
                state = adv_obj.state
                if state=='approve':
                    amount += adv_obj.advance
                for result in input_line_ids:
                    if state == 'approve' and amount != 0 and result.get('code') == 'SAR':
                        result['amount'] = amount
        lon_obj = self.env['hr.loan'].search([('employee_id', '=', employee.id), ('state', '=', 'approve')])
        for loan in lon_obj:
            for loan_line in loan.loan_lines:
                if date_from <= loan_line.date <= date_to and not loan_line.paid:
                    for result in input_line_ids:
                        if result.get('code') == 'LO':
                            result['amount'] = loan_line.amount
                            result['loan_line_id'] = loan_line.id

        res['value'].update({
            'worked_days_line_ids': worked_days_line_ids,
            'input_line_ids': input_line_ids,
        })
        return res
    @api.model
    def get_worked_day_lines(self, contracts, date_from, date_to,sheet_id=False):

        """
        @param contract: Browse record of contracts
        @return: returns a list of dict containing the input that should be applied for the given contract between date_from and date_to
        """
        res = []
        # fill only if the contract as a working schedule linked
        for contract in contracts:
            if sheet_id:
                attendances = {
                    'name': _("Normal Working Days paid at 100%"),
                    'sequence': 1,
                    'code': 'WORK100',
                    'number_of_days': sheet_id.no_wd,
                    'number_of_hours': sheet_id.tot_wh,
                    'contract_id': contract.id,
                }
            else:
                attendances = {
                    'name': _("Normal Working Days paid at 100%"),
                    'sequence': 1,
                    'code': 'WORK100',
                    'number_of_days': 0,
                    'number_of_hours': 0,
                    'contract_id': contract.id,
                }

            res.append(attendances)
        return res
    def action_payslip_cancel(self):

        # if self.filtered(lambda slip: slip.state == 'done'):
        #     raise UserError(_("Cannot cancel a payslip that is done."))
        if self.payslip_id.move_id:
            self.payslip_id.move_id.sudo().button_cancel()
        return self.write({'state': 'cancel'})