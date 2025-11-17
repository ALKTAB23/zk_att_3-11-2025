# 🚨 حل عاجل - تنفيذ فوري

## المشكلة
Odoo لا يستطيع قراءة الملف بسبب صلاحيات خاطئة.

---

## ✅ الحل (نسخ والصق فقط)

### افتح Terminal على السيرفر وانسخ الأوامر التالية:

```bash
# 1. إيقاف Odoo
systemctl stop odoo

# 2. تصحيح صلاحيات oh_hr_zk_attendance
chown -R odoo:odoo /opt/odoo16/custom/oh_hr_zk_attendance
chmod -R 755 /opt/odoo16/custom/oh_hr_zk_attendance
find /opt/odoo16/custom/oh_hr_zk_attendance -type f -name "*.py" -exec chmod 644 {} \;

# 3. تصحيح صلاحيات hr_shifts_custom
chown -R odoo:odoo /opt/odoo16/custom/hr_shifts_custom
chmod -R 755 /opt/odoo16/custom/hr_shifts_custom
find /opt/odoo16/custom/hr_shifts_custom -type f -name "*.py" -exec chmod 644 {} \;

# 4. تشغيل Odoo
systemctl start odoo

# 5. متابعة اللوج
tail -f /var/log/odoo/odoo.log
```

**انتهى!** اضغط `Ctrl+C` لإيقاف اللوج عندما يبدأ Odoo بالعمل.

---

## 🔍 التحقق السريع

بعد تنفيذ الأوامر، تحقق من الصلاحيات:

```bash
ls -la /opt/odoo16/custom/oh_hr_zk_attendance/models/zk_machine.py
```

**يجب أن تظهر:**
```
-rw-r--r-- 1 odoo odoo ... zk_machine.py
```

✅ `odoo odoo` = المالك صحيح  
✅ `rw-r--r--` = الصلاحيات صحيحة (644)

---

## ⚠️ إذا لم يعمل

جرب هذا الأمر المباشر:

```bash
chmod 644 /opt/odoo16/custom/oh_hr_zk_attendance/models/zk_machine.py
chown odoo:odoo /opt/odoo16/custom/oh_hr_zk_attendance/models/zk_machine.py
systemctl restart odoo
```

---

## 📞 تشخيص إضافي

إذا استمرت المشكلة، شارك ناتج هذا الأمر:

```bash
ls -la /opt/odoo16/custom/oh_hr_zk_attendance/models/zk_machine.py
ps aux | grep odoo | grep -v grep
```
