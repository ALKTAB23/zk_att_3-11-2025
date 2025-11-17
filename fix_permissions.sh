#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# Script إصلاح صلاحيات الملفات - Permission Error Fix
# ═══════════════════════════════════════════════════════════════════

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║          🔐 إصلاح صلاحيات ملفات Odoo Modules                 ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# التحقق من أننا root
if [ "$EUID" -ne 0 ]; then 
   echo "❌ يجب تشغيل هذا الـ Script بصلاحيات root"
   echo "   استخدم: sudo ./fix_permissions.sh"
   exit 1
fi

# ═══════════════════════════════════════════════════════════════════
# تصحيح صلاحيات hr_shifts_custom
# ═══════════════════════════════════════════════════════════════════
echo "┌────────────────────────────────────────────────────────────────┐"
echo "│ 📁 hr_shifts_custom                                            │"
echo "└────────────────────────────────────────────────────────────────┘"

MODULE1="/opt/odoo16/custom/hr_shifts_custom"

if [ -d "$MODULE1" ]; then
    echo "⚙️  تعيين المالك إلى odoo:odoo..."
    chown -R odoo:odoo "$MODULE1"
    
    echo "⚙️  تعيين صلاحيات المجلدات (755)..."
    find "$MODULE1" -type d -exec chmod 755 {} \;
    
    echo "⚙️  تعيين صلاحيات ملفات Python (644)..."
    find "$MODULE1" -type f -name "*.py" -exec chmod 644 {} \;
    
    echo "⚙️  تعيين صلاحيات ملفات XML (644)..."
    find "$MODULE1" -type f -name "*.xml" -exec chmod 644 {} \;
    
    echo "✅ تم تصحيح صلاحيات hr_shifts_custom"
else
    echo "⚠️  المجلد غير موجود: $MODULE1"
fi

echo ""

# ═══════════════════════════════════════════════════════════════════
# تصحيح صلاحيات oh_hr_zk_attendance
# ═══════════════════════════════════════════════════════════════════
echo "┌────────────────────────────────────────────────────────────────┐"
echo "│ 📁 oh_hr_zk_attendance                                         │"
echo "└────────────────────────────────────────────────────────────────┘"

MODULE2="/opt/odoo16/custom/oh_hr_zk_attendance"

if [ -d "$MODULE2" ]; then
    echo "⚙️  تعيين المالك إلى odoo:odoo..."
    chown -R odoo:odoo "$MODULE2"
    
    echo "⚙️  تعيين صلاحيات المجلدات (755)..."
    find "$MODULE2" -type d -exec chmod 755 {} \;
    
    echo "⚙️  تعيين صلاحيات ملفات Python (644)..."
    find "$MODULE2" -type f -name "*.py" -exec chmod 644 {} \;
    
    echo "⚙️  تعيين صلاحيات ملفات XML (644)..."
    find "$MODULE2" -type f -name "*.xml" -exec chmod 644 {} \;
    
    # تأكيد خاص للملف الذي يسبب المشكلة
    echo "⚙️  التحقق من zk_machine.py..."
    ZK_FILE="$MODULE2/models/zk_machine.py"
    if [ -f "$ZK_FILE" ]; then
        chown odoo:odoo "$ZK_FILE"
        chmod 644 "$ZK_FILE"
        echo "   ✅ $ZK_FILE - Owner: $(stat -c '%U:%G' "$ZK_FILE"), Permissions: $(stat -c '%a' "$ZK_FILE")"
    fi
    
    echo "✅ تم تصحيح صلاحيات oh_hr_zk_attendance"
else
    echo "⚠️  المجلد غير موجود: $MODULE2"
fi

echo ""

# ═══════════════════════════════════════════════════════════════════
# عرض ملخص الصلاحيات
# ═══════════════════════════════════════════════════════════════════
echo "┌────────────────────────────────────────────────────────────────┐"
echo "│ 📊 ملخص الصلاحيات                                             │"
echo "└────────────────────────────────────────────────────────────────┘"

echo ""
echo "🔍 hr_shifts_custom/models/hr_payroll_custom.py:"
FILE1="$MODULE1/models/hr_payroll_custom.py"
if [ -f "$FILE1" ]; then
    echo "   Owner: $(stat -c '%U:%G' "$FILE1")"
    echo "   Permissions: $(stat -c '%a' "$FILE1")"
else
    echo "   ⚠️  الملف غير موجود"
fi

echo ""
echo "🔍 oh_hr_zk_attendance/models/zk_machine.py:"
FILE2="$MODULE2/models/zk_machine.py"
if [ -f "$FILE2" ]; then
    echo "   Owner: $(stat -c '%U:%G' "$FILE2")"
    echo "   Permissions: $(stat -c '%a' "$FILE2")"
else
    echo "   ⚠️  الملف غير موجود"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║              ✅ اكتمل تصحيح الصلاحيات                        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "📋 الخطوة التالية:"
echo "   أعد تشغيل Odoo: systemctl restart odoo"
echo ""
