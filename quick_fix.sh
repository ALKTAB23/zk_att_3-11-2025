#!/bin/bash
# Quick Fix - تشغيل فوري

echo "🔧 إصلاح سريع للصلاحيات..."
echo ""

# إيقاف Odoo
echo "1️⃣  إيقاف Odoo..."
systemctl stop odoo
sleep 2

# تصحيح الصلاحيات
echo "2️⃣  تصحيح صلاحيات oh_hr_zk_attendance..."
chown -R odoo:odoo /opt/odoo16/custom/oh_hr_zk_attendance
chmod -R 755 /opt/odoo16/custom/oh_hr_zk_attendance
find /opt/odoo16/custom/oh_hr_zk_attendance -type f -name "*.py" -exec chmod 644 {} \;

echo "3️⃣  تصحيح صلاحيات hr_shifts_custom..."
chown -R odoo:odoo /opt/odoo16/custom/hr_shifts_custom
chmod -R 755 /opt/odoo16/custom/hr_shifts_custom
find /opt/odoo16/custom/hr_shifts_custom -type f -name "*.py" -exec chmod 644 {} \;

# تشغيل Odoo
echo "4️⃣  تشغيل Odoo..."
systemctl start odoo

echo ""
echo "✅ تم الإصلاح!"
echo ""
echo "⏳ انتظر 10-15 ثانية ثم افتح Odoo في المتصفح"
echo ""
echo "📋 لمتابعة اللوج:"
echo "   tail -f /var/log/odoo/odoo.log"
