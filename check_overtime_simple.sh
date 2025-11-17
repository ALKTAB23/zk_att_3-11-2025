#!/bin/bash
# Script بسيط للتحقق من بيانات Overtime مباشرة من قاعدة البيانات

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     🔍 فحص بيانات Overtime من قاعدة البيانات                 ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# التحقق من وجود psql
if ! command -v psql &> /dev/null; then
    echo "❌ psql غير مثبت"
    exit 1
fi

# اسم قاعدة البيانات
DB_NAME="Ahmed_2_11"

echo "📊 البحث عن سجلات hr.attendance لموظف IBRA في أكتوبر 2025..."
echo ""

# استعلام SQL
psql -U odoo -d "$DB_NAME" -c "
SELECT 
    he.name AS employee_name,
    ha.check_in::date AS attendance_date,
    TO_CHAR(ha.check_in, 'HH24:MI') AS check_in_time,
    TO_CHAR(ha.check_out, 'HH24:MI') AS check_out_time,
    ROUND(CAST(ha.act_delay_time AS numeric), 2) AS delay_hours,
    ROUND(CAST(ha.act_diff_time AS numeric), 2) AS diff_hours,
    ROUND(CAST(ha.act_over_time AS numeric), 2) AS overtime_hours
FROM 
    hr_attendance ha
    JOIN hr_employee he ON ha.employee_id = he.id
WHERE 
    he.name ILIKE '%IBRA%'
    AND ha.check_in >= '2025-10-01'
    AND ha.check_in < '2025-11-01'
    AND ha.check_out IS NOT NULL
ORDER BY 
    ha.check_in;
"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "📊 إحصائيات الإضافي:"
echo "═══════════════════════════════════════════════════════════════"

psql -U odoo -d "$DB_NAME" -c "
SELECT 
    COUNT(*) AS total_days,
    COUNT(CASE WHEN ha.act_over_time > 0 THEN 1 END) AS days_with_overtime,
    ROUND(CAST(SUM(ha.act_over_time) AS numeric), 2) AS total_overtime_hours
FROM 
    hr_attendance ha
    JOIN hr_employee he ON ha.employee_id = he.id
WHERE 
    he.name ILIKE '%IBRA%'
    AND ha.check_in >= '2025-10-01'
    AND ha.check_in < '2025-11-01'
    AND ha.check_out IS NOT NULL;
"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "🔍 فحص سجلات Attendance Sheet Lines:"
echo "═══════════════════════════════════════════════════════════════"

psql -U odoo -d "$DB_NAME" -c "
SELECT 
    asl.date AS attendance_date,
    ROUND(CAST(asl.overtime AS numeric), 2) AS overtime_in_sheet_line,
    ROUND(CAST(ha.act_over_time AS numeric), 2) AS overtime_in_hr_attendance,
    asl.status
FROM 
    attendance_sheet_line asl
    LEFT JOIN hr_attendance ha ON asl.hr_attendance_id = ha.id
    JOIN attendance_sheet ash ON asl.attendance_sheet_id = ash.id
    JOIN hr_employee he ON ash.employee_id = he.id
WHERE 
    he.name ILIKE '%IBRA%'
    AND asl.date >= '2025-10-01'
    AND asl.date < '2025-11-01'
ORDER BY 
    asl.date
LIMIT 10;
"

echo ""
echo "✅ انتهى الفحص"
