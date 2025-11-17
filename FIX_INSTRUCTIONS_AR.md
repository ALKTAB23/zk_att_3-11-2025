# 🔧 تعليمات إصلاح الأخطاء البرمجية

## المشاكل المكتشفة

### 1. خطأ Payslip Cancel
عند الضغط على Cancel في Payslip، يظهر خطأ:
```
AttributeError: 'hr.payslip' object has no attribute 'payslip_id'
```

**السبب:** خطأ برمجي في `/opt/odoo16/custom/hr_shifts_custom/models/hr_payroll_custom.py`  
السطر 137 يستخدم `self.payslip_id.move_id` بينما يجب أن يكون `self.move_id`

### 2. خطأ Download Attendance
عند تحميل بيانات الحضور من الجهاز، يظهر خطأ:
```
NameError: name '_logger' is not defined
```

**السبب:** في `/opt/odoo16/custom/oh_hr_zk_attendance/models/zk_machine.py`  
لم يتم تعريف `_logger` على مستوى الملف، مما يسبب خطأ في `register_attendances()`

---

## الحل - الطريقة 1: باستخدام Script التلقائي

### الخطوات:

1. **انسخ الملف `fix_payslip_cancel.patch` إلى السيرفر:**
   ```bash
   scp fix_payslip_cancel.patch root@192.168.1.172:/tmp/
   ```

2. **سجل دخول إلى السيرفر:**
   ```bash
   ssh root@192.168.1.172
   ```

3. **شغل الـ Script:**
   ```bash
   cd /tmp
   chmod +x fix_payslip_cancel.patch
   ./fix_payslip_cancel.patch
   ```

4. **انتظر 15 ثانية لإعادة تشغيل Odoo**

5. **اختبر الحل:**
   - افتح أي Payslip
   - اضغط على Cancel
   - يجب أن يعمل بدون أخطاء

---

## الحل - الطريقة 2: يدوياً

### الخطوات:

1. **سجل دخول إلى السيرفر:**
   ```bash
   ssh root@192.168.1.172
   ```

2. **افتح الملف للتعديل:**
   ```bash
   nano /opt/odoo16/custom/hr_shifts_custom/models/hr_payroll_custom.py
   ```

3. **ابحث عن السطر 137:**
   اضغط `Ctrl+W` ثم اكتب: `payslip_id.move_id`

4. **استبدل السطور التالية:**
   
   **❌ القديم (خطأ):**
   ```python
   if self.payslip_id.move_id:
       self.payslip_id.move_id.sudo().button_cancel()
   ```
   
   **✅ الجديد (صحيح):**
   ```python
   if self.move_id:
       self.move_id.sudo().button_cancel()
   ```

5. **احفظ الملف:**
   - اضغط `Ctrl+O` ثم `Enter` للحفظ
   - اضغط `Ctrl+X` للخروج

6. **أعد تشغيل Odoo:**
   ```bash
   systemctl restart odoo
   ```

7. **انتظر 15 ثانية ثم اختبر الحل**

---

## الحل - الطريقة 3: باستخدام Git (الأفضل والأشمل)

### الخطوات:

1. **سجل دخول إلى السيرفر:**
   ```bash
   ssh root@192.168.1.172
   ```

2. **تحديث كلا الـ Modules:**
   
   **أ. تحديث hr_shifts_custom (إصلاح Payslip Cancel):**
   ```bash
   cd /opt/odoo16/custom/hr_shifts_custom
   git stash  # احفظ أي تغييرات محلية
   git pull origin main
   ```
   
   **ب. تحديث oh_hr_zk_attendance (إصلاح Download Attendance):**
   ```bash
   cd /opt/odoo16/custom/oh_hr_zk_attendance
   git stash  # احفظ أي تغييرات محلية
   git pull origin main
   ```

3. **أعد تشغيل Odoo:**
   ```bash
   systemctl restart odoo
   ```

4. **انتظر 15 ثانية ثم اختبر الحلول**

---

## التحقق من الحلول

بعد تطبيق أي طريقة من الطرق أعلاه، تحقق من:

### ✅ اختبار إصلاح Payslip Cancel:

1. **التحقق من الكود:**
   ```bash
   grep -n "if self.move_id:" /opt/odoo16/custom/hr_shifts_custom/models/hr_payroll_custom.py
   ```
   يجب أن يظهر السطر 137 مع `self.move_id`

2. **الاختبار الفعلي:**
   - افتح أي Payslip في Odoo
   - اضغط Cancel
   - يجب أن يعمل بدون أخطاء ✅

### ✅ اختبار إصلاح Download Attendance:

1. **التحقق من الكود:**
   ```bash
   grep -n "_logger = logging.getLogger" /opt/odoo16/custom/oh_hr_zk_attendance/models/zk_machine.py
   ```
   يجب أن يظهر السطر 42 مع `_logger = logging.getLogger(__name__)`

2. **الاختبار الفعلي:**
   - اذهب إلى Attendance > ZK Machine
   - اختر جهاز
   - اضغط "Download Attendance"
   - يجب أن يعمل بدون أخطاء ✅

### ✅ التحقق العام من اللوج:
```bash
tail -f /var/log/odoo/odoo.log | grep -E "payslip_id|_logger"
```
يجب ألا تظهر أخطاء تحتوي على هذه الكلمات

---

## الدعم

إذا واجهت أي مشكلة:
1. راجع لوج Odoo: `tail -f /var/log/odoo/odoo.log`
2. تأكد من إعادة تشغيل Odoo بعد التعديل
3. تأكد من أن الملف `/opt/odoo16/custom/hr_shifts_custom/models/hr_payroll_custom.py` يحتوي على الكود الصحيح

---

## معلومات إضافية

### Commits:
- **إصلاح Payslip Cancel:** 695eee8
- **إصلاح Download Attendance:** 7310cfb

### روابط GitHub:
- **المستودع:** https://github.com/ALKTAB23/zk_att_3-11-2025
- **Commit Payslip:** https://github.com/ALKTAB23/zk_att_3-11-2025/commit/695eee8
- **Commit Attendance:** https://github.com/ALKTAB23/zk_att_3-11-2025/commit/7310cfb

### التاريخ:
2025-11-17

### الملفات المعدلة:
1. `hr_shifts_custom/models/hr_payroll_custom.py` - إصلاح `self.payslip_id.move_id`
2. `oh_hr_zk_attendance/models/zk_machine.py` - إضافة `_logger` على مستوى الملف
