#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# Script إصلاح شامل لجميع الأخطاء البرمجية
# ═══════════════════════════════════════════════════════════════════

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     🔧 إصلاح شامل لأخطاء Odoo - ZK Attendance System        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# ═══════════════════════════════════════════════════════════════════
# إصلاح 0: تصحيح صلاحيات الملفات
# ═══════════════════════════════════════════════════════════════════
echo "┌────────────────────────────────────────────────────────────────┐"
echo "│ 0️⃣  تصحيح صلاحيات الملفات                                    │"
echo "└────────────────────────────────────────────────────────────────┘"

echo "⚙️  تعيين الصلاحيات الصحيحة للملفات..."

# تصحيح صلاحيات hr_shifts_custom
chown -R odoo:odoo /opt/odoo16/custom/hr_shifts_custom
chmod -R 755 /opt/odoo16/custom/hr_shifts_custom
find /opt/odoo16/custom/hr_shifts_custom -type f -name "*.py" -exec chmod 644 {} \;

echo "✅ تم تصحيح صلاحيات hr_shifts_custom"

# تصحيح صلاحيات oh_hr_zk_attendance
chown -R odoo:odoo /opt/odoo16/custom/oh_hr_zk_attendance
chmod -R 755 /opt/odoo16/custom/oh_hr_zk_attendance
find /opt/odoo16/custom/oh_hr_zk_attendance -type f -name "*.py" -exec chmod 644 {} \;

echo "✅ تم تصحيح صلاحيات oh_hr_zk_attendance"
echo ""

# ═══════════════════════════════════════════════════════════════════
# إصلاح 1: Payslip Cancel Error
# ═══════════════════════════════════════════════════════════════════
echo "┌────────────────────────────────────────────────────────────────┐"
echo "│ 1️⃣  إصلاح Payslip Cancel Error                                │"
echo "└────────────────────────────────────────────────────────────────┘"

FILE1="/opt/odoo16/custom/hr_shifts_custom/models/hr_payroll_custom.py"

if [ ! -f "$FILE1" ]; then
    echo "❌ الملف غير موجود: $FILE1"
else
    # نسخة احتياطية
    cp "$FILE1" "$FILE1.backup_$(date +%Y%m%d_%H%M%S)"
    echo "✅ تم عمل نسخة احتياطية: $FILE1.backup_$(date +%Y%m%d_%H%M%S)"
    
    # إصلاح الخطأ
    sed -i 's/if self\.payslip_id\.move_id:/if self.move_id:/g' "$FILE1"
    sed -i 's/self\.payslip_id\.move_id\.sudo()/self.move_id.sudo()/g' "$FILE1"
    
    # التحقق
    if grep -q "if self.move_id:" "$FILE1"; then
        echo "✅ تم إصلاح Payslip Cancel Error بنجاح"
    else
        echo "⚠️  فشل في تطبيق الإصلاح - الرجاء المراجعة اليدوية"
    fi
fi

echo ""

# ═══════════════════════════════════════════════════════════════════
# إصلاح 2: Download Attendance _logger Error
# ═══════════════════════════════════════════════════════════════════
echo "┌────────────────────────────────────────────────────────────────┐"
echo "│ 2️⃣  إصلاح Download Attendance _logger Error                  │"
echo "└────────────────────────────────────────────────────────────────┘"

FILE2="/opt/odoo16/custom/oh_hr_zk_attendance/models/zk_machine.py"

if [ ! -f "$FILE2" ]; then
    echo "❌ الملف غير موجود: $FILE2"
else
    # نسخة احتياطية
    cp "$FILE2" "$FILE2.backup_$(date +%Y%m%d_%H%M%S)"
    echo "✅ تم عمل نسخة احتياطية: $FILE2.backup_$(date +%Y%m%d_%H%M%S)"
    
    # التحقق من وجود _logger على مستوى الملف
    if grep -q "^_logger = logging.getLogger(__name__)$" "$FILE2"; then
        echo "✅ _logger موجود بالفعل على مستوى الملف"
    else
        echo "⚙️  إضافة _logger على مستوى الملف..."
        
        # إيجاد السطر المناسب للإضافة (بعد from odoo.addons.base.models.res_partner import _tz_get)
        LINE_NUM=$(grep -n "from odoo.addons.base.models.res_partner import _tz_get" "$FILE2" | cut -d: -f1)
        
        if [ -n "$LINE_NUM" ]; then
            # إضافة _logger بعد السطر المحدد
            TEMP_FILE=$(mktemp)
            awk -v line="$LINE_NUM" '
                NR == line {
                    print $0
                    print ""
                    print "_logger = logging.getLogger(__name__)"
                    print ""
                    next
                }
                { print }
            ' "$FILE2" > "$TEMP_FILE"
            mv "$TEMP_FILE" "$FILE2"
            
            echo "✅ تم إضافة _logger بعد السطر $LINE_NUM"
        else
            echo "⚠️  لم يتم العثور على السطر المناسب للإضافة"
            echo "⚠️  الرجاء الإضافة يدوياً بعد imports"
        fi
    fi
    
    # إزالة التعريفات المحلية المكررة
    echo "⚙️  إزالة التعريفات المحلية المكررة..."
    sed -i '/^[[:space:]]*_logger = logging\.getLogger(__name__)$/d' "$FILE2"
    
    # إعادة إضافة التعريف على مستوى الملف إذا تم حذفه بالخطأ
    if ! grep -q "^_logger = logging.getLogger(__name__)$" "$FILE2"; then
        LINE_NUM=$(grep -n "from odoo.addons.base.models.res_partner import _tz_get" "$FILE2" | cut -d: -f1)
        if [ -n "$LINE_NUM" ]; then
            TEMP_FILE=$(mktemp)
            awk -v line="$LINE_NUM" '
                NR == line {
                    print $0
                    print ""
                    print "_logger = logging.getLogger(__name__)"
                    print ""
                    next
                }
                { print }
            ' "$FILE2" > "$TEMP_FILE"
            mv "$TEMP_FILE" "$FILE2"
        fi
    fi
    
    # التحقق النهائي
    if grep -q "^_logger = logging.getLogger(__name__)$" "$FILE2"; then
        echo "✅ تم إصلاح _logger Error بنجاح"
        
        # عرض رقم السطر
        LOGGER_LINE=$(grep -n "^_logger = logging.getLogger(__name__)$" "$FILE2" | cut -d: -f1)
        echo "   📍 _logger في السطر: $LOGGER_LINE"
    else
        echo "⚠️  فشل في تطبيق الإصلاح - الرجاء المراجعة اليدوية"
    fi
fi

echo ""

# ═══════════════════════════════════════════════════════════════════
# إعادة تشغيل Odoo
# ═══════════════════════════════════════════════════════════════════
echo "┌────────────────────────────────────────────────────────────────┐"
echo "│ 3️⃣  إعادة تشغيل Odoo                                          │"
echo "└────────────────────────────────────────────────────────────────┘"

systemctl restart odoo

if [ $? -eq 0 ]; then
    echo "✅ تم إعادة تشغيل Odoo بنجاح"
    echo ""
    echo "⏳ الرجاء الانتظار 15-20 ثانية لإعادة تشغيل Odoo..."
else
    echo "❌ فشل في إعادة تشغيل Odoo"
    echo "⚠️  الرجاء تشغيله يدوياً: systemctl restart odoo"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    ✅ اكتمل الإصلاح                           ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "📋 الخطوات التالية:"
echo "   1. انتظر 15-20 ثانية"
echo "   2. افتح Odoo في المتصفح"
echo "   3. اختبر Payslip Cancel"
echo "   4. اختبر Download Attendance"
echo ""
echo "📊 للتحقق من اللوج:"
echo "   tail -f /var/log/odoo/odoo.log"
echo ""
