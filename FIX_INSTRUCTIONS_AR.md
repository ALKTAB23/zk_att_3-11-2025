# 🔧 تعليمات إصلاح خطأ Payslip Cancel

## المشكلة
عند الضغط على Cancel في Payslip، يظهر خطأ:
```
AttributeError: 'hr.payslip' object has no attribute 'payslip_id'
```

## السبب
خطأ برمجي في `/opt/odoo16/custom/hr_shifts_custom/models/hr_payroll_custom.py`  
السطر 137 يستخدم `self.payslip_id.move_id` بينما يجب أن يكون `self.move_id`

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

## الحل - الطريقة 3: باستخدام Git (الأفضل)

### الخطوات:

1. **سجل دخول إلى السيرفر:**
   ```bash
   ssh root@192.168.1.172
   ```

2. **انتقل إلى مجلد الكود:**
   ```bash
   cd /opt/odoo16/custom/hr_shifts_custom
   ```

3. **احفظ أي تغييرات محلية (إن وجدت):**
   ```bash
   git stash
   ```

4. **اسحب آخر تحديثات من GitHub:**
   ```bash
   git pull origin main
   ```

5. **أعد تشغيل Odoo:**
   ```bash
   systemctl restart odoo
   ```

6. **انتظر 15 ثانية ثم اختبر الحل**

---

## التحقق من الحل

بعد تطبيق أي طريقة من الطرق أعلاه، تحقق من:

1. ✅ **لا توجد أخطاء في اللوج:**
   ```bash
   tail -f /var/log/odoo/odoo.log | grep payslip_id
   ```
   يجب ألا تظهر كلمة `payslip_id` في الأخطاء

2. ✅ **الكود تم تحديثه:**
   ```bash
   grep -n "if self.move_id:" /opt/odoo16/custom/hr_shifts_custom/models/hr_payroll_custom.py
   ```
   يجب أن يظهر السطر 137 مع `self.move_id`

3. ✅ **Payslip Cancel يعمل:**
   - افتح أي Payslip في Odoo
   - اضغط Cancel
   - لا توجد أخطاء

---

## الدعم

إذا واجهت أي مشكلة:
1. راجع لوج Odoo: `tail -f /var/log/odoo/odoo.log`
2. تأكد من إعادة تشغيل Odoo بعد التعديل
3. تأكد من أن الملف `/opt/odoo16/custom/hr_shifts_custom/models/hr_payroll_custom.py` يحتوي على الكود الصحيح

---

## معلومات إضافية

- **Commit ID:** 695eee8
- **GitHub:** https://github.com/ALKTAB23/zk_att_3-11-2025
- **التاريخ:** 2025-11-17
