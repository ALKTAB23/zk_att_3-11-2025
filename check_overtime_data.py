#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script للتحقق من بيانات Overtime في hr.attendance

طريقة التشغيل:
cd /opt/odoo16
sudo -u odoo ./odoo-bin shell -c /etc/odoo/odoo.conf -d Ahmed_2_11 < /tmp/check_overtime_data.py
"""

import sys

# التحقق من وجود env
if 'env' not in dir():
    print("❌ هذا الـ Script يجب تشغيله في Odoo Shell")
    print("   استخدم: sudo -u odoo ./odoo-bin shell -c /etc/odoo/odoo.conf -d Ahmed_2_11 < script.py")
    sys.exit(1)

print("\n" + "="*80)
print("🔍 فحص بيانات Overtime لموظف IBRA في أكتوبر 2025")
print("="*80)

# البحث عن الموظف
employee = env['hr.employee'].search([('name', 'ilike', 'IBRA')], limit=1)

if not employee:
    print("❌ لم يتم العثور على الموظف IBRA")
    exit()

print(f"\n✅ الموظف: {employee.name} (ID: {employee.id})")

# البحث عن سجلات الحضور
attendances = env['hr.attendance'].search([
    ('employee_id', '=', employee.id),
    ('check_in', '>=', '2025-10-01 00:00:00'),
    ('check_in', '<=', '2025-10-31 23:59:59'),
    ('check_out', '!=', False),
], order='check_in')

print(f"📊 عدد السجلات: {len(attendances)}")
print("\n" + "-"*80)

# تحليل كل سجل
has_overtime = False
total_overtime = 0.0
overtime_days = 0

for att in attendances:
    # الحصول على الشفت
    zk_machine = env['zk.machine'].search([], limit=1)
    if not zk_machine:
        continue
    
    date_str = str(att.check_in)
    match_shift = env['zk.machine'].get_match_shift(date_str, employee.id)
    
    if not match_shift or not match_shift.hr_shift:
        continue
    
    # حساب الأوقات
    checkin_float = zk_machine._get_float_from_time(att.check_in)
    checkout_float = zk_machine._get_float_from_time(att.check_out)
    
    # وقت الخروج المخطط
    planned_checkout = match_shift.pl_sign_out
    
    # الفرق
    diff = checkout_float - planned_checkout
    
    # عرض التفاصيل
    print(f"\n📅 {att.check_in.date()} - {att.check_in.strftime('%A')}")
    print(f"   Check In:  {att.check_in.strftime('%H:%M')} (Planned: {zk_machine.get_time_from_float(match_shift.pl_sign_in)})")
    print(f"   Check Out: {att.check_out.strftime('%H:%M')} (Planned: {zk_machine.get_time_from_float(planned_checkout)})")
    
    if diff > 0:
        print(f"   ⏰ تأخير في الخروج: {diff:.2f}h ({int(diff*60)} دقيقة)")
        print(f"   💰 Overtime في DB: {att.act_over_time:.2f}h")
        
        if att.act_over_time > 0:
            has_overtime = True
            total_overtime += att.act_over_time
            overtime_days += 1
            print(f"   ✅ يوجد إضافي مُسجّل")
        else:
            print(f"   ⚠️  يجب أن يكون هناك إضافي لكنه = 0!")
    elif diff < 0:
        print(f"   ⬅️  خروج مبكر: {abs(diff):.2f}h ({int(abs(diff)*60)} دقيقة)")
    else:
        print(f"   ✅ خروج في الوقت المحدد")

print("\n" + "="*80)
print("📊 الملخص:")
print("="*80)
print(f"إجمالي الأيام: {len(attendances)}")
print(f"الأيام التي لها إضافي: {overtime_days}")
print(f"إجمالي ساعات الإضافي: {total_overtime:.2f}h")

if not has_overtime:
    print("\n⚠️  لا يوجد أي إضافي مُسجّل في قاعدة البيانات!")
    print("   السبب المحتمل:")
    print("   1. الموظف يخرج دائماً قبل أو في الوقت المحدد")
    print("   2. الكود الجديد لحساب الإضافي لم يتم تطبيقه")
    print("   3. تحتاج لإعادة تنزيل البيانات من الجهاز")

print("\n" + "="*80)
