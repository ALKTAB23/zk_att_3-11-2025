# دليل الموظف متعدد المناطق
# Multi-Zone Employee Guide

## 🎯 الهدف / Purpose

تمكين الموظفين من العمل في أكثر من Zone (منطقة) والبصم في أي جهاز ضمن المناطق المُصرح لهم بها.

Enable employees to work in multiple Zones and punch in any device within their authorized zones.

---

## 📋 السيناريو / Scenario

### مثال عملي / Practical Example

**الموظف:** أحمد محمد
**Employee:** Ahmed Mohamed

**المناطق المُصرح بها:**
- Zone A: طرابلس - المكتب الرئيسي (Tripoli - Main Office)
- Zone B: بنغازي - الفرع (Benghazi - Branch)

**الأجهزة:**
- Device 1 في Zone A (IP: 192.168.1.10)
- Device 2 في Zone B (IP: 192.168.2.20)

**سجل الحضور:**

| التاريخ / Date | المنطقة / Zone | الحضور / Check In | الانصراف / Check Out | ساعات العمل / Work Hours |
|---------------|----------------|-------------------|---------------------|-------------------------|
| 2025-11-04 | Zone A (Tripoli) | 09:00 | 17:00 | 8 hours |
| 2025-11-05 | Zone B (Benghazi) | 08:30 | 16:30 | 8 hours |
| 2025-11-06 | Zone A (Tripoli) | 09:15 | 17:15 | 8 hours |
| 2025-11-07 | Zone B (Benghazi) | 08:00 | 16:00 | 8 hours |

**النتيجة:**
- التقرير يُظهر الموظف حضر في Zone A يومين وZone B يومين
- كل zone لها حقوق وواجبات حسب Policy الخاصة بها
- الراتب يُحسب بناءً على Rules لكل Zone

---

## 🔧 الإعداد / Setup

### 1. إنشاء المناطق / Create Zones

```
القائمة: Attendances > Biometric Manager > Device Zones
Menu: Attendances > Biometric Manager > Device Zones
```

**Zone A - Tripoli:**
- Zone Name: Tripoli - Main Office
- Zone Code: LY-TPL
- Timezone: Africa/Tripoli

**Zone B - Benghazi:**
- Zone Name: Benghazi - Branch
- Zone Code: LY-BGZ
- Timezone: Africa/Tripoli

---

### 2. ربط الأجهزة بالمناطق / Link Devices to Zones

```
القائمة: Attendances > Biometric Manager > Device Configuration
Menu: Attendances > Biometric Manager > Device Configuration
```

**Device 1:**
- Machine IP: 192.168.1.10
- Port: 4370
- **Device Zone:** Tripoli - Main Office ✅
- Timezone: Africa/Tripoli (auto-filled)

**Device 2:**
- Machine IP: 192.168.2.20
- Port: 4370
- **Device Zone:** Benghazi - Branch ✅
- Timezone: Africa/Tripoli (auto-filled)

---

### 3. تحديد المناطق المُصرح بها للموظف / Set Employee Authorized Zones

```
القائمة: Employees > [Select Employee] > HR Settings
Menu: Employees > [Select Employee] > HR Settings
```

**في صفحة الموظف / In Employee Form:**

1. ابحث عن حقل **"Authorized Zones"**
2. اختر المناطق التي يُسمح للموظف العمل بها:
   - ✅ Tripoli - Main Office
   - ✅ Benghazi - Branch
3. احفظ / Save

**مهم:** إذا تركت الحقل فارغاً = الموظف يستطيع البصم في أي Zone
**Important:** If left empty = Employee can punch in ANY zone

---

### 4. ربط الموظف بأجهزة البصمة / Link Employee to Devices

**في نفس صفحة الموظف / Same Employee Form:**

في قسم **"Biometric Devices ID"**:

| Machine IP | Device ID |
|------------|-----------|
| 192.168.1.10 (Tripoli) | 1001 |
| 192.168.2.20 (Benghazi) | 1001 |

**ملاحظة:** Device ID هو رقم الموظف في الجهاز (نفس الرقم في كلا الجهازين عادة)
**Note:** Device ID is the employee's number in the device (usually same in both devices)

---

## 📊 عرض التقارير / Viewing Reports

### 1. تقرير الحضور حسب المنطقة / Attendance Report by Zone

```
القائمة: Attendances > Biometric Manager > Attendance log
Menu: Attendances > Biometric Manager > Attendance log
```

**الفلاتر المتاحة / Available Filters:**
- 🔍 Filter by Zone: اختر منطقة معينة / Select specific zone
- 👤 Filter by Employee: اختر موظف معين / Select specific employee
- 📅 Filter by Date: اختر نطاق تاريخ / Select date range

**Group By:**
- By Zone: عرض حسب المنطقة / View by zone
- By Employee: عرض حسب الموظف / View by employee
- By Date: عرض حسب التاريخ / View by date

---

### 2. مثال على التقرير / Report Example

**Group By Zone:**

```
📍 Zone A - Tripoli Main Office
   👤 Ahmed Mohamed
      📅 2025-11-04  09:00 → 17:00  (8h)
      📅 2025-11-06  09:15 → 17:15  (8h)

📍 Zone B - Benghazi Branch
   👤 Ahmed Mohamed
      📅 2025-11-05  08:30 → 16:30  (8h)
      📅 2025-11-07  08:00 → 16:00  (8h)
```

---

## 🔒 التحقق الأمني / Security Validation

### 1. التحقق التلقائي / Automatic Validation

عند تحميل الحضور من الجهاز:

```python
if employee.authorized_zone_ids:
    if device.zone_id not in employee.authorized_zone_ids:
        ⚠️ Warning logged: Employee not authorized in this zone
```

**ماذا يحدث؟ / What happens?**
- ✅ الحضور يُسجل عادياً / Attendance is recorded normally
- ⚠️ يُسجل تحذير في الـ Logs / Warning logged
- 📋 يمكن مراجعة التحذيرات لاحقاً / Can review warnings later

**لماذا لا يتم رفض الحضور؟ / Why not reject?**
- قد يكون هناك حالة طارئة / May be emergency
- قد يكون الموظف في مهمة عمل / May be on work assignment
- الـ HR Manager يراجع ويُصحح / HR Manager reviews and corrects

---

### 2. مراجعة التحذيرات / Review Warnings

```
القائمة: Settings > Technical > Logging
Menu: Settings > Technical > Logging
```

**البحث عن:** "not authorized in this zone"
**Search for:** "not authorized in this zone"

**مثال على Log:**
```
WARNING: Employee Ahmed Mohamed (ID: 123) punched in Zone 'Benghazi Branch' 
but is not authorized. Authorized zones: Tripoli Main Office
```

---

## 📐 حساب الحقوق والواجبات / Rights & Obligations Calculation

### كيف تُحسب الحقوق حسب Zone؟ / How are rights calculated per Zone?

**السيناريو:**
- Zone A Policy: Overtime after 8 hours
- Zone B Policy: Overtime after 7 hours

**النتيجة:**
```
Ahmed worked in Zone A on 2025-11-04:
  Work hours: 8 hours
  Overtime: 0 hours (Policy: after 8h)
  
Ahmed worked in Zone B on 2025-11-05:
  Work hours: 8 hours
  Overtime: 1 hour (Policy: after 7h) ✅
```

**ملاحظة:** الـ Policy rules تُطبق حسب Zone الحضور
**Note:** Policy rules are applied based on attendance Zone

---

## 🎯 حالات الاستخدام / Use Cases

### 1. موظف ميداني / Field Employee

**المثال:** مهندس صيانة
**Example:** Maintenance Engineer

- يزور Site A صباحاً / Visits Site A in morning
- يزور Site B بعد الظهر / Visits Site B in afternoon
- Authorized in both zones
- يُسجل حضوره في كل موقع / Records attendance at each location

---

### 2. موظف إداري متنقل / Mobile Administrative Staff

**المثال:** مدير إقليمي
**Example:** Regional Manager

- يعمل في Main Office (Zone A) 3 أيام
- يزور Branch (Zone B) يومين
- Authorized zones: A, B, C
- كل زيارة مُسجلة بـ Zone الخاصة بها

---

### 3. موظف بمهام خاصة / Special Assignment Employee

**المثال:** موظف مُعار مؤقتاً
**Example:** Temporarily Assigned Employee

- Zone الأساسي: Main Office
- Zone المؤقت: Branch (for 2 months)
- Add both zones to authorized list
- بعد انتهاء المهمة: إزالة Zone المؤقت / After mission: Remove temporary zone

---

## ⚙️ الإعدادات المتقدمة / Advanced Settings

### 1. تقييد الموظفين في Zone واحدة / Restrict to Single Zone

**الإعداد:**
- لا تُضف Zones للموظف / Don't add zones to employee
- اترك "Authorized Zones" فارغ / Leave "Authorized Zones" empty
- OR add only ONE zone

**النتيجة:**
- ممكن الموظف يبصم في أي Zone / Employee can punch anywhere (if empty)
- أو فقط في Zone المُحددة / Or only in specified zone (if one added)

---

### 2. موظفين بدون قيود / Unrestricted Employees

**مثل:** HR Manager, CEO

**الإعداد:**
- اترك "Authorized Zones" فارغ
- Leave "Authorized Zones" empty

**النتيجة:**
- يستطيع البصم في أي Zone
- Can punch in any zone
- لا توجد تحذيرات
- No warnings

---

## 📊 التقارير المتقدمة / Advanced Reports

### 1. تقرير الموظف حسب Zone / Employee Report by Zone

**SQL Query Example:**
```sql
SELECT 
    e.name as employee,
    z.name as zone,
    DATE(a.punching_day) as date,
    COUNT(*) as attendance_count,
    SUM(a.worked_hours) as total_hours
FROM zk_machine_attendance a
JOIN hr_employee e ON e.id = a.employee_id
LEFT JOIN zk_device_zone z ON z.id = a.zone_id
WHERE a.punching_day >= '2025-11-01'
GROUP BY e.name, z.name, DATE(a.punching_day)
ORDER BY e.name, date;
```

---

### 2. تحليل Zone Usage / Zone Usage Analysis

```sql
SELECT 
    z.name as zone,
    COUNT(DISTINCT a.employee_id) as unique_employees,
    COUNT(*) as total_punches,
    DATE(a.punching_day) as date
FROM zk_machine_attendance a
LEFT JOIN zk_device_zone z ON z.id = a.zone_id
WHERE a.punching_day >= '2025-11-01'
GROUP BY z.name, DATE(a.punching_day)
ORDER BY date, z.name;
```

---

## 🔍 استكشاف الأخطاء / Troubleshooting

### مشكلة: الموظف لا يستطيع البصم / Problem: Employee Cannot Punch

**الحل:**
1. ✅ تحقق من Device ID صحيح / Check Device ID is correct
2. ✅ تحقق من الموظف مُضاف للجهاز / Check employee added to device
3. ✅ تحقق من Authorized Zones (أو فارغ) / Check Authorized Zones (or empty)

---

### مشكلة: Zone لا تظهر في التقرير / Problem: Zone not shown in report

**الحل:**
1. ✅ تحقق من الجهاز مربوط بـ Zone / Check device linked to zone
2. ✅ أعد تحميل البيانات من الجهاز / Re-download data from device
3. ✅ تحقق من zone_id في zk_machine_attendance / Check zone_id in records

---

### مشكلة: تحذيرات غير صحيحة / Problem: Incorrect Warnings

**الحل:**
1. ✅ راجع Authorized Zones للموظف / Review employee's Authorized Zones
2. ✅ أضف Zones المفقودة / Add missing zones
3. ✅ احفظ التعديلات / Save changes

---

## 📝 الملخص / Summary

### الميزات الرئيسية / Key Features

✅ **موظف واحد → zones متعددة**
   One employee → Multiple zones

✅ **تتبع تلقائي للـ Zone في كل حضور**
   Automatic zone tracking per attendance

✅ **تقارير مفصلة حسب Zone**
   Detailed reports by zone

✅ **تحقق أمني من الصلاحيات**
   Security validation of authorizations

✅ **Policy rules منفصلة لكل Zone**
   Separate policy rules per zone

✅ **سهولة في الإدارة والمراجعة**
   Easy management and review

---

## 🎓 أفضل الممارسات / Best Practices

### 1. تخطيط المناطق / Zone Planning
- حدد Zones حسب المواقع الجغرافية / Define zones by geographic location
- استخدم Zone Codes واضحة / Use clear zone codes
- وثق Policy لكل Zone / Document policy per zone

### 2. إدارة الصلاحيات / Authorization Management
- راجع Authorized Zones دورياً / Review authorized zones regularly
- احذف Zones القديمة / Remove old zones
- وثق التغييرات / Document changes

### 3. المراقبة / Monitoring
- راجع Logs أسبوعياً / Review logs weekly
- تحقق من التحذيرات / Check warnings
- صحح الأخطاء فوراً / Correct errors immediately

---

**Last Updated:** 2025-11-04
**Version:** 1.0
**Status:** ✅ Implemented - Multi-Zone Employee Feature Active
