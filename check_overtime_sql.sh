#!/bin/bash
# SQL Diagnostic Script for Overtime Issue
# =========================================

DB_NAME="odoo16_zk"  # Update with actual database name
DB_USER="odoo16"     # Update with actual database user

echo "========================================================================"
echo "🔍 تشخيص مشكلة احتساب الإضافي - فحص قاعدة البيانات"
echo "========================================================================"

echo ""
echo "1️⃣ البحث عن الموظف IBRA..."
psql -U $DB_USER -d $DB_NAME -c "
SELECT id, name, barcode 
FROM hr_employee 
WHERE name ILIKE '%IBRA%' 
LIMIT 5;
"

echo ""
echo "2️⃣ فحص سجلات hr.attendance للموظف في أكتوبر 2025..."
psql -U $DB_USER -d $DB_NAME -c "
SELECT 
    a.id,
    e.name as employee,
    a.attendance_date,
    to_char(a.check_in, 'HH24:MI') as check_in_time,
    to_char(a.check_out, 'HH24:MI') as check_out_time,
    ROUND(a.worked_hours::numeric, 2) as worked_hours,
    ROUND(a.act_over_time::numeric, 2) as overtime
FROM hr_attendance a
JOIN hr_employee e ON e.id = a.employee_id
WHERE e.name ILIKE '%IBRA%'
  AND a.attendance_date BETWEEN '2025-10-12' AND '2025-10-13'
ORDER BY a.attendance_date DESC, a.check_in DESC
LIMIT 10;
"

echo ""
echo "3️⃣ فحص سجلات attendance_sheet_line للموظف..."
psql -U $DB_USER -d $DB_NAME -c "
SELECT 
    l.id,
    e.name as employee,
    l.date,
    ROUND(l.ac_sign_in::numeric, 2) as actual_in,
    ROUND(l.ac_sign_out::numeric, 2) as actual_out,
    ROUND(l.pl_sign_out::numeric, 2) as planned_out,
    ROUND(l.worked_hours::numeric, 2) as worked_hours,
    ROUND(l.overtime::numeric, 2) as overtime,
    l.status
FROM attendance_sheet_line l
JOIN hr_employee e ON e.id = l.employee_id
WHERE e.name ILIKE '%IBRA%'
  AND l.date BETWEEN '2025-10-12' AND '2025-10-13'
ORDER BY l.date DESC
LIMIT 10;
"

echo ""
echo "4️⃣ فحص Attendance Policy للموظف..."
psql -U $DB_USER -d $DB_NAME -c "
SELECT 
    p.id,
    p.name,
    p.overtime_policy
FROM hr_attendance_policy p
WHERE p.id IN (
    SELECT DISTINCT line_att_policy_id 
    FROM attendance_sheet_line l
    JOIN hr_employee e ON e.id = l.employee_id
    WHERE e.name ILIKE '%IBRA%'
      AND l.date BETWEEN '2025-10-01' AND '2025-10-31'
)
LIMIT 5;
"

echo ""
echo "5️⃣ فحص قواعد الإضافي (Overtime Rules)..."
psql -U $DB_USER -d $DB_NAME -c "
SELECT 
    r.id,
    p.name as policy_name,
    r.type,
    ROUND(r.active_after::numeric, 2) as apply_after_hours,
    ROUND(r.rate::numeric, 2) as rate
FROM att_policy_overtime_rule r
JOIN hr_attendance_policy p ON p.id = r.att_policy_id
WHERE p.id IN (
    SELECT DISTINCT line_att_policy_id 
    FROM attendance_sheet_line l
    JOIN hr_employee e ON e.id = l.employee_id
    WHERE e.name ILIKE '%IBRA%'
      AND l.date BETWEEN '2025-10-01' AND '2025-10-31'
)
ORDER BY p.name, r.type;
"

echo ""
echo "6️⃣ فحص العقد والجدول الزمني..."
psql -U $DB_USER -d $DB_NAME -c "
SELECT 
    c.id as contract_id,
    e.name as employee,
    c.name as contract_name,
    c.state as contract_state,
    rc.name as calendar_name,
    c.date_start,
    c.date_end
FROM hr_contract c
JOIN hr_employee e ON e.id = c.employee_id
LEFT JOIN resource_calendar rc ON rc.id = c.resource_calendar_id
WHERE e.name ILIKE '%IBRA%'
  AND c.state = 'open'
LIMIT 5;
"

echo ""
echo "========================================================================"
echo "✅ انتهى الفحص"
echo "========================================================================"
