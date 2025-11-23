#!/usr/bin/env python3
"""
Diagnostic Script for Attendance Policy Application
====================================================
Checks why late_in, diff_time, forget are showing 00:00
"""

import sys
import logging
from datetime import datetime, date

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
_logger = logging.getLogger(__name__)

def run_diagnostic():
    """Run diagnostic checks on attendance sheet policy application."""
    
    try:
        import odoo
        from odoo import api, SUPERUSER_ID
        
        # Connect to Odoo database
        db_name = 'odoo16_zk'  # Update with actual DB name
        
        _logger.info("=" * 80)
        _logger.info("🔍 تشخيص تطبيق Attendance Policy")
        _logger.info("=" * 80)
        
        with api.Environment.manage():
            registry = odoo.registry(db_name)
            with registry.cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, {})
                
                # 1. البحث عن Attendance Sheet لـ IBRA في أكتوبر 2025
                _logger.info("\n1️⃣ البحث عن Attendance Sheet...")
                
                employee = env['hr.employee'].search([
                    ('name', 'ilike', 'IBRA')
                ], limit=1)
                
                if not employee:
                    _logger.error("❌ لم يتم العثور على الموظف IBRA")
                    return
                
                att_sheet = env['attendance.sheet'].search([
                    ('employee_id', '=', employee.id),
                    ('date_from', '>=', date(2025, 10, 1)),
                    ('date_to', '<=', date(2025, 10, 31)),
                ], limit=1)
                
                if not att_sheet:
                    _logger.error("❌ لم يتم العثور على Attendance Sheet")
                    return
                
                _logger.info(f"✅ Sheet: {att_sheet.name}")
                _logger.info(f"   State: {att_sheet.state}")
                _logger.info(f"   Sheet Action: {att_sheet.sheet_action}")
                
                # 2. فحص Attendance Policy
                _logger.info("\n2️⃣ فحص Attendance Policy...")
                
                if not att_sheet.contract_id:
                    _logger.error("❌ لا يوجد contract مرتبط بالـ Sheet")
                    return
                
                _logger.info(f"✅ Contract: {att_sheet.contract_id.name}")
                
                # البحث عن Policy من shift schedule
                shift_schedules = env['hr.shift.schedule'].search([
                    ('employee_id', '=', employee.id),
                    ('start_date', '<=', att_sheet.date_to),
                    '|',
                    ('end_date', '>=', att_sheet.date_from),
                    ('end_date', '=', False),
                ])
                
                if not shift_schedules:
                    _logger.error("❌ لا يوجد Shift Schedule للموظف")
                    return
                
                _logger.info(f"✅ عدد Shift Schedules: {len(shift_schedules)}")
                
                for schedule in shift_schedules:
                    _logger.info(f"\n   📅 Schedule: {schedule.name}")
                    
                    # فحص تفاصيل الورديات
                    details = env['hr.shift.schedule.detail'].search([
                        ('schedule_id', '=', schedule.id),
                        ('date', '>=', att_sheet.date_from),
                        ('date', '<=', att_sheet.date_to),
                    ], limit=5)
                    
                    for detail in details:
                        _logger.info(f"\n      📅 {detail.date}:")
                        
                        if detail.shift_id:
                            _logger.info(f"         Shift: {detail.shift_id.name}")
                            
                            if detail.shift_id.att_policy_id:
                                policy = detail.shift_id.att_policy_id
                                _logger.info(f"         ✅ Policy: {policy.name}")
                                
                                # فحص Late Rules
                                if policy.late_rule_id:
                                    _logger.info(f"            📋 Late Rule: {policy.late_rule_id.name}")
                                    _logger.info(f"               عدد القواعد: {len(policy.late_rule_id.line_ids)}")
                                    
                                    for rule in policy.late_rule_id.line_ids:
                                        _logger.info(f"               • Counter: {rule.counter}, Time: {rule.time:.2f}h - {rule.time_limit:.2f}h, Type: {rule.type}, Rate: {rule.rate}, Amount: {rule.amount}")
                                else:
                                    _logger.warning("            ⚠️ لا توجد Late Rules!")
                                
                                # فحص Diff Rules
                                if policy.diff_rule_id:
                                    _logger.info(f"            📋 Diff Rule: {policy.diff_rule_id.name}")
                                    _logger.info(f"               عدد القواعد: {len(policy.diff_rule_id.line_ids)}")
                                else:
                                    _logger.warning("            ⚠️ لا توجد Diff Rules!")
                                
                                # فحص Forget Rules
                                if policy.forget_rule_id:
                                    _logger.info(f"            📋 Forget Rule: {policy.forget_rule_id.name}")
                                    _logger.info(f"               عدد القواعد: {len(policy.forget_rule_id.line_ids)}")
                                else:
                                    _logger.warning("            ⚠️ لا توجد Forget Rules!")
                            else:
                                _logger.warning(f"         ⚠️ لا توجد Attendance Policy مرتبطة بالـ Shift!")
                        else:
                            _logger.warning(f"         ⚠️ لا توجد وردية لهذا اليوم!")
                
                # 3. فحص Attendance Sheet Lines
                _logger.info("\n3️⃣ فحص Attendance Sheet Lines...")
                
                lines_with_late = att_sheet.att_sheet_line_ids.filtered(lambda l: l.act_late_in > 0)
                
                _logger.info(f"✅ عدد الأيام بتأخير: {len(lines_with_late)}")
                
                for line in lines_with_late[:3]:  # أول 3 أيام فقط
                    _logger.info(f"\n   📅 {line.date}:")
                    _logger.info(f"      act_late_in: {line.act_late_in:.2f}h")
                    _logger.info(f"      late_in (Policy Applied): {line.late_in:.2f}")
                    _logger.info(f"      Status: {line.status}")
                    
                    if line.line_att_policy_id:
                        _logger.info(f"      Policy: {line.line_att_policy_id.name}")
                    else:
                        _logger.warning(f"      ⚠️ لا توجد Policy مرتبطة بهذا السطر!")
                
                # 4. الإحصائيات النهائية
                _logger.info("\n4️⃣ الإحصائيات النهائية:")
                _logger.info(f"   Total Late Hours (Policy): {att_sheet.late_policy_hours:.2f}h")
                _logger.info(f"   Total Diff Hours (Policy): {att_sheet.diff_policy_hours:.2f}h")
                _logger.info(f"   Total Forget Hours: {att_sheet.forget_hours:.2f}h")
                _logger.info(f"   Total Overtime: {att_sheet.tot_overtime:.2f}h")
                _logger.info(f"   No of Absence Days: {att_sheet.no_absence}")
                
                # 5. التوصيات
                _logger.info("\n" + "=" * 80)
                _logger.info("💡 التوصيات:")
                _logger.info("=" * 80)
                
                if att_sheet.late_policy_hours == 0 and len(lines_with_late) > 0:
                    _logger.warning("⚠️ يوجد تأخير لكن late_policy_hours = 0")
                    _logger.info("   الأسباب المحتملة:")
                    _logger.info("   1. Late Rules غير مطبقة أو غير موجودة")
                    _logger.info("   2. Counter غير متطابق")
                    _logger.info("   3. Time Range لا يشمل التأخير الفعلي")
                    _logger.info("\n   الحل:")
                    _logger.info("   1. تأكد من وجود Late Rules في Attendance Policy")
                    _logger.info("   2. تأكد من Counter = 1, 2, 3... حسب عدد مرات التأخير")
                    _logger.info("   3. تأكد من Time Range يشمل قيم act_late_in الفعلية")
                    _logger.info("   4. أعد حساب Attendance Sheet بعد التأكد من القواعد")
                
                _logger.info("\n" + "=" * 80)
                _logger.info("✅ انتهى التشخيص")
                _logger.info("=" * 80)
                
    except Exception as e:
        _logger.error(f"❌ خطأ في التشخيص: {e}", exc_info=True)


if __name__ == '__main__':
    run_diagnostic()
