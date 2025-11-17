#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnostic Script for Attendance Transfer Issues
-------------------------------------------------
This script checks why attendance records from zk.machine.attendance
are not being transferred to hr.attendance.
"""

import sys
import os

# Add Odoo to path
sys.path.append('/home/user/webapp/zk_att_3-11-2025')

def check_requirements():
    """Check if records exist and what's blocking transfer"""
    
    print("=" * 80)
    print("🔍 ATTENDANCE TRANSFER DIAGNOSTIC")
    print("=" * 80)
    
    print("\n📋 SQL Queries to run in Odoo database:\n")
    
    # Check 1: Unprocessed records
    query1 = """
-- ✅ CHECK 1: Records waiting to be processed
SELECT 
    COUNT(*) as unprocessed_count,
    COUNT(DISTINCT punching_day) as days_count,
    COUNT(DISTINCT employee_id) as employees_count,
    MIN(punching_day) as earliest_date,
    MAX(punching_day) as latest_date
FROM zk_machine_attendance
WHERE is_process = False;
"""
    
    # Check 2: Which employees have unprocessed records
    query2 = """
-- ✅ CHECK 2: Which employees have unprocessed records?
SELECT 
    e.id as employee_id,
    e.name as employee_name,
    e.device_id as device_id,
    COUNT(*) as record_count,
    MIN(zk.punching_day) as first_date,
    MAX(zk.punching_day) as last_date
FROM zk_machine_attendance zk
JOIN hr_employee e ON zk.employee_id = e.id
WHERE zk.is_process = False
GROUP BY e.id, e.name, e.device_id
ORDER BY e.name;
"""
    
    # Check 3: Contract status for these employees
    query3 = """
-- ⚠ CHECK 3: Do these employees have ACTIVE contracts?
SELECT 
    e.id as employee_id,
    e.name as employee_name,
    COALESCE(c.id, 0) as contract_id,
    COALESCE(c.state, 'NO CONTRACT') as contract_state,
    COALESCE(c.date_start::text, 'N/A') as contract_start,
    COALESCE(c.date_end::text, 'No end date') as contract_end
FROM hr_employee e
LEFT JOIN hr_contract c ON c.employee_id = e.id AND c.state = 'open'
WHERE e.id IN (
    SELECT DISTINCT employee_id 
    FROM zk_machine_attendance 
    WHERE is_process = False
)
ORDER BY e.name;
"""
    
    # Check 4: Shift schedule assignment
    query4 = """
-- ⚠ CHECK 4: Do these employees have SHIFT SCHEDULES?
SELECT 
    e.id as employee_id,
    e.name as employee_name,
    c.id as contract_id,
    COALESCE(ss.id, 0) as schedule_id,
    COALESCE(hs.name, 'NO SHIFT ASSIGNED') as shift_name,
    COALESCE(ss.start_date::text, 'N/A') as schedule_start,
    COALESCE(ss.end_date::text, 'No end') as schedule_end,
    COALESCE(ss.active::text, 'N/A') as is_active
FROM hr_employee e
JOIN hr_contract c ON c.employee_id = e.id AND c.state = 'open'
LEFT JOIN attendance_sheet ss ON ss.rel_hr_schedule = c.id AND ss.active = True
LEFT JOIN hr_shift hs ON ss.hr_shift = hs.id
WHERE e.id IN (
    SELECT DISTINCT employee_id 
    FROM zk_machine_attendance 
    WHERE is_process = False
)
ORDER BY e.name;
"""
    
    # Check 5: Sample of unprocessed records
    query5 = """
-- 📅 CHECK 5: Sample of unprocessed records
SELECT 
    zk.id,
    e.name as employee_name,
    zk.punching_day,
    zk.punching_time,
    zk.punch_type,
    zk.is_process,
    m.name as machine_name
FROM zk_machine_attendance zk
JOIN hr_employee e ON zk.employee_id = e.id
LEFT JOIN zk_machine m ON zk.machine_ip = m.id
WHERE zk.is_process = False
ORDER BY zk.punching_time DESC
LIMIT 20;
"""
    
    print(query1)
    print("\n" + "=" * 80 + "\n")
    print(query2)
    print("\n" + "=" * 80 + "\n")
    print(query3)
    print("\n" + "=" * 80 + "\n")
    print(query4)
    print("\n" + "=" * 80 + "\n")
    print(query5)
    
    print("\n" + "=" * 80)
    print("📖 HOW TO USE:")
    print("=" * 80)
    print("""
1. Copy each SQL query above
2. Run in Odoo database (psql or pgAdmin)
3. Check the results:

   ✅ IF CHECK 1 shows count = 0:
      → All records already processed
      → Click "Download Data" to fetch new records from device
   
   ⚠ IF CHECK 3 shows "NO CONTRACT":
      → Employee needs an ACTIVE contract (state='open')
      → Go to: Employees → Contracts → Create/Activate contract
   
   ⚠ IF CHECK 4 shows "NO SHIFT ASSIGNED":
      → Employee needs a shift schedule
      → Go to: Attendance Sheet → Assign shift to employee's contract
      → Make sure: start_date <= current date AND active = True
   
   ✅ IF both contract and shift exist:
      → The issue is in get_match_shift() logic
      → Check shift configuration matches attendance date/time
""")
    
    print("\n" + "=" * 80)
    print("🔧 QUICK FIXES:")
    print("=" * 80)
    print("""
FIX 1 - Create Active Contract:
--------------------------------
UPDATE hr_contract 
SET state = 'open' 
WHERE employee_id = [EMPLOYEE_ID] 
  AND id = [CONTRACT_ID];

FIX 2 - Activate Shift Schedule:
---------------------------------
UPDATE attendance_sheet 
SET active = True 
WHERE rel_hr_schedule = [CONTRACT_ID] 
  AND hr_shift = [SHIFT_ID];

FIX 3 - Reset is_process to retry transfer:
--------------------------------------------
UPDATE zk_machine_attendance 
SET is_process = False 
WHERE employee_id = [EMPLOYEE_ID] 
  AND punching_day = '[DATE]';
""")
    
    print("\n" + "=" * 80)
    print("✅ DONE - Copy SQL queries above and run them")
    print("=" * 80)

if __name__ == "__main__":
    check_requirements()
