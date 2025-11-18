#!/usr/bin/env python3
"""
Diagnostic Script for Overtime Calculation Issue
=================================================
This script checks why overtime is showing 00:00 despite late checkout.

Checks:
1. hr.attendance records for the employee
2. act_over_time field values
3. attendance_sheet_line records
4. overtime field values
5. Attendance Policy configuration
6. Policy active_after and rate settings
"""

import sys
import logging
from datetime import datetime, date

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
_logger = logging.getLogger(__name__)

def run_diagnostic():
    """Run diagnostic checks on overtime calculation."""
    
    try:
        import odoo
        from odoo import api, SUPERUSER_ID
        
        # Connect to Odoo database
        db_name = 'odoo16_zk'  # Update with actual DB name
        
        _logger.info("=" * 80)
        _logger.info("🔍 تشخيص مشكلة احتساب الإضافي")
        _logger.info("=" * 80)
        
        with api.Environment.manage():
            registry = odoo.registry(db_name)
            with registry.cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, {})
                
                # 1. البحث عن موظف IBRA
                _logger.info("\n1️⃣ البحث عن الموظف IBRA...")
                employee = env['hr.employee'].search([
                    ('name', 'ilike', 'IBRA')
                ], limit=1)
                
                if not employee:
                    _logger.error("❌ لم يتم العثور على الموظف IBRA")
                    return
                
                _logger.info(f"✅ تم العثور على: {employee.name} (ID: {employee.id})")
                
                # 2. فحص سجلات الحضور في أكتوبر 2025
                _logger.info("\n2️⃣ فحص سجلات الحضور (hr.attendance) في أكتوبر 2025...")
                
                date_from = date(2025, 10, 12)
                date_to = date(2025, 10, 13)
                
                attendances = env['hr.attendance'].search([
                    ('employee_id', '=', employee.id),
                    ('attendance_date', '>=', date_from),
                    ('attendance_date', '<=', date_to),
                ], order='attendance_date desc, check_in desc')
                
                if not attendances:
                    _logger.warning("⚠️ لا توجد سجلات حضور لهذا الموظف في هذا التاريخ")
                else:
                    _logger.info(f"✅ تم العثور على {len(attendances)} سجل حضور")
                    
                    for att in attendances:
                        _logger.info("-" * 60)
                        _logger.info(f"📅 التاريخ: {att.attendance_date}")
                        _logger.info(f"🕐 الدخول: {att.check_in}")
                        _logger.info(f"🕐 الخروج: {att.check_out}")
                        _logger.info(f"⏱️  ساعات العمل: {att.worked_hours:.2f}h")
                        _logger.info(f"💰 الإضافي (act_over_time): {att.act_over_time:.2f}h")
                        
                        if hasattr(att, 'att_policy_id') and att.att_policy_id:
                            _logger.info(f"📋 السياسة المطبقة: {att.att_policy_id.name}")
                
                # 3. فحص سجلات Attendance Sheet
                _logger.info("\n3️⃣ فحص سجلات Attendance Sheet...")
                
                sheet_lines = env['attendance.sheet.line'].search([
                    ('employee_id', '=', employee.id),
                    ('date', '>=', date_from),
                    ('date', '<=', date_to),
                ], order='date desc')
                
                if not sheet_lines:
                    _logger.warning("⚠️ لا توجد سجلات Attendance Sheet لهذا الموظف")
                else:
                    _logger.info(f"✅ تم العثور على {len(sheet_lines)} سجل في Attendance Sheet")
                    
                    for line in sheet_lines:
                        _logger.info("-" * 60)
                        _logger.info(f"📅 التاريخ: {line.date}")
                        _logger.info(f"🕐 الدخول الفعلي: {line.ac_sign_in:.2f} ({_format_time(line.ac_sign_in)})")
                        _logger.info(f"🕐 الخروج الفعلي: {line.ac_sign_out:.2f} ({_format_time(line.ac_sign_out)})")
                        _logger.info(f"🕐 الخروج المخطط: {line.pl_sign_out:.2f} ({_format_time(line.pl_sign_out)})")
                        _logger.info(f"⏱️  ساعات العمل: {line.worked_hours:.2f}h")
                        _logger.info(f"💰 الإضافي (overtime): {line.overtime:.2f}h")
                        _logger.info(f"📊 الحالة: {line.status}")
                        
                        if line.line_att_policy_id:
                            policy = line.line_att_policy_id
                            _logger.info(f"📋 السياسة: {policy.name}")
                            
                            # فحص قواعد الإضافي
                            overtime_rules = policy.overtime_rule_ids.filtered(
                                lambda r: r.type == 'workday'
                            )
                            if overtime_rules:
                                for rule in overtime_rules:
                                    _logger.info(f"   ⚙️ قاعدة الإضافي:")
                                    _logger.info(f"      - Apply After: {rule.active_after:.2f}h ({_format_time(rule.active_after)})")
                                    _logger.info(f"      - Rate: {rule.rate}x")
                
                # 4. فحص إعدادات Attendance Policy
                _logger.info("\n4️⃣ فحص إعدادات Attendance Policy للموظف...")
                
                # البحث عن العقد النشط
                contract = env['hr.contract'].search([
                    ('employee_id', '=', employee.id),
                    ('state', '=', 'open'),
                ], limit=1)
                
                if contract:
                    _logger.info(f"✅ عقد نشط: {contract.name}")
                    
                    if contract.resource_calendar_id:
                        _logger.info(f"📅 جدول العمل: {contract.resource_calendar_id.name}")
                        
                        # فحص الورديات المرتبطة بالسياسات
                        shift_schedules = env['hr.shift.schedule'].search([
                            ('employee_id', '=', employee.id),
                            ('start_date', '<=', date_to),
                            '|',
                            ('end_date', '>=', date_from),
                            ('end_date', '=', False),
                        ])
                        
                        if shift_schedules:
                            for schedule in shift_schedules:
                                _logger.info(f"\n📅 جدول الورديات: {schedule.name}")
                                _logger.info(f"   من: {schedule.start_date} إلى: {schedule.end_date or 'مفتوح'}")
                                
                                # فحص تفاصيل الوردية
                                details = env['hr.shift.schedule.detail'].search([
                                    ('schedule_id', '=', schedule.id),
                                    ('date', '>=', date_from),
                                    ('date', '<=', date_to),
                                ])
                                
                                for detail in details:
                                    _logger.info(f"\n   📅 {detail.date}:")
                                    _logger.info(f"      - الوردية: {detail.shift_id.name if detail.shift_id else 'N/A'}")
                                    
                                    if detail.shift_id and detail.shift_id.att_policy_id:
                                        policy = detail.shift_id.att_policy_id
                                        _logger.info(f"      - السياسة: {policy.name}")
                                        
                                        overtime_rules = policy.overtime_rule_ids.filtered(
                                            lambda r: r.type == 'workday'
                                        )
                                        
                                        if overtime_rules:
                                            _logger.info(f"      - قواعد الإضافي:")
                                            for rule in overtime_rules:
                                                _logger.info(f"         • Apply After: {rule.active_after:.2f}h ({_format_time(rule.active_after)})")
                                                _logger.info(f"         • Rate: {rule.rate}x")
                                        else:
                                            _logger.warning("      ⚠️ لا توجد قواعد إضافي!")
                        else:
                            _logger.warning("⚠️ لا يوجد جدول ورديات للموظف")
                    else:
                        _logger.warning("⚠️ لا يوجد جدول عمل مرتبط بالعقد")
                else:
                    _logger.warning("⚠️ لا يوجد عقد نشط للموظف")
                
                # 5. التوصيات
                _logger.info("\n" + "=" * 80)
                _logger.info("💡 التوصيات:")
                _logger.info("=" * 80)
                
                if attendances and all(att.act_over_time == 0 for att in attendances):
                    _logger.warning("⚠️ جميع سجلات hr.attendance تحتوي على act_over_time = 0")
                    _logger.info("   👉 الحل: يجب إعادة تنزيل الحضور من الجهاز الحيوي")
                    _logger.info("   👉 الخطوات:")
                    _logger.info("      1. حذف سجلات الحضور الحالية من hr.attendance")
                    _logger.info("      2. إعادة تنزيل الحضور من ZK Device")
                    _logger.info("      3. التأكد من تطبيق الكود المحدث")
                
                if sheet_lines and all(line.overtime == 0 for line in sheet_lines):
                    _logger.warning("⚠️ جميع سجلات Attendance Sheet تحتوي على overtime = 0")
                    _logger.info("   👉 الحل: يجب إعادة إنشاء Attendance Sheet")
                    _logger.info("   👉 الخطوات:")
                    _logger.info("      1. حذف Attendance Sheet الحالي")
                    _logger.info("      2. إنشاء Attendance Sheet جديد")
                    _logger.info("      3. التأكد من وجود Attendance Policy صحيحة")
                
                if not contract or not contract.resource_calendar_id:
                    _logger.error("❌ لا يوجد عقد نشط أو جدول عمل للموظف")
                    _logger.info("   👉 الحل: إنشاء عقد نشط مع جدول عمل")
                
                _logger.info("\n" + "=" * 80)
                _logger.info("✅ انتهى التشخيص")
                _logger.info("=" * 80)
                
    except Exception as e:
        _logger.error(f"❌ خطأ في التشخيص: {e}", exc_info=True)


def _format_time(float_time):
    """Convert float time to HH:MM format."""
    if float_time < 0:
        return "N/A"
    hours = int(float_time)
    minutes = int((float_time - hours) * 60)
    return f"{hours:02d}:{minutes:02d}"


if __name__ == '__main__':
    run_diagnostic()
