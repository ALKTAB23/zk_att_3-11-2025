#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script لإعادة حساب Overtime لسجلات hr.attendance الموجودة
يجب تشغيله في Odoo Shell:
/opt/odoo16/odoo-bin shell -c /etc/odoo/odoo.conf -d Ahmed_2_11 < recalculate_overtime.py
"""

import logging
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

def recalculate_overtime_for_attendances():
    """إعادة حساب Overtime لجميع السجلات في أكتوبر 2025"""
    
    print("\n" + "="*80)
    print("🔄 إعادة حساب Overtime لسجلات hr.attendance")
    print("="*80)
    
    # البحث عن سجلات الحضور في أكتوبر 2025
    attendances = env['hr.attendance'].search([
        ('check_in', '>=', '2025-10-01 00:00:00'),
        ('check_in', '<=', '2025-10-31 23:59:59'),
        ('check_out', '!=', False),  # فقط السجلات التي لها check_out
    ], order='check_in')
    
    print(f"\n📊 عدد السجلات المراد إعادة حسابها: {len(attendances)}")
    
    if not attendances:
        print("⚠️  لا توجد سجلات لإعادة الحساب")
        return
    
    # إحصائيات
    updated_count = 0
    with_overtime_count = 0
    total_overtime = 0.0
    
    # إعادة حساب كل سجل
    for att in attendances:
        try:
            # الحصول على معلومات الموظف والشفت
            employee = att.employee_id
            check_in = att.check_in
            check_out = att.check_out
            
            if not check_out:
                continue
            
            # البحث عن الشفت المطابق
            zk_machine = env['zk.machine'].search([], limit=1)
            if not zk_machine:
                print("⚠️  لم يتم العثور على ZK Machine")
                continue
            
            # استدعاء دالة حساب الإضافي من zk_machine
            date_str = str(check_in)
            match_shift = env['zk.machine'].get_match_shift(date_str, employee.id)
            
            if not match_shift or not match_shift.hr_shift:
                continue
            
            # حساب الإضافي باستخدام الدالة الموجودة
            checkin_float = zk_machine._get_float_from_time(check_in)
            checkout_float = zk_machine._get_float_from_time(check_out)
            
            delay, diff, overtime = zk_machine.calculate_delay_diff_overtime(
                match_shift, 
                checkin_float, 
                checkout_float, 
                match_shift.hr_shift
            )
            
            # تحديث السجل إذا تغير الإضافي
            if overtime != att.act_over_time:
                att.write({
                    'act_over_time': overtime,
                    'act_delay_time': delay,
                    'act_diff_time': diff,
                })
                updated_count += 1
                
                if overtime > 0:
                    with_overtime_count += 1
                    total_overtime += overtime
                    print(f"✅ {employee.name} - {check_in.date()}: Overtime = {overtime:.2f}h")
        
        except Exception as e:
            print(f"❌ خطأ في معالجة {att.id}: {str(e)}")
            continue
    
    # طباعة الإحصائيات
    print("\n" + "="*80)
    print("📊 النتائج:")
    print("="*80)
    print(f"إجمالي السجلات: {len(attendances)}")
    print(f"السجلات المحدثة: {updated_count}")
    print(f"السجلات التي لديها إضافي: {with_overtime_count}")
    print(f"إجمالي ساعات الإضافي: {total_overtime:.2f}h")
    print("="*80)
    
    # Commit التغييرات
    env.cr.commit()
    print("\n✅ تم حفظ التغييرات في قاعدة البيانات")

# تشغيل السكريبت
if __name__ == '__main__':
    recalculate_overtime_for_attendances()
