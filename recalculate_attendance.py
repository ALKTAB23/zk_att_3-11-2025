#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to recalculate act_delay_time, act_diff_time, act_over_time for existing hr.attendance records
Usage: Run from Odoo shell or scheduled action
"""

import sys
import os

# Add Odoo to path
sys.path.insert(0, '/opt/odoo16')

try:
    import odoo
    from odoo import api, SUPERUSER_ID
    
    def recalculate_attendance(db_name='odoo16'):
        """Recalculate delay/diff/overtime for all attendance records"""
        
        # Initialize Odoo
        odoo.tools.config.parse_config(['-c', '/etc/odoo16/odoo.conf'])
        
        with odoo.api.Environment.manage():
            registry = odoo.registry(db_name)
            with registry.cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, {})
                
                # Get ZK Machine model
                ZKMachine = env['zk.machine']
                
                # Get all attendance records that need recalculation
                # Filter: has check_in and check_out, but act_over_time = 0 or NULL
                Attendance = env['hr.attendance']
                
                # Find records with both check_in and check_out
                attendances = Attendance.search([
                    ('check_in', '!=', False),
                    ('check_out', '!=', False),
                    '|',
                    ('act_over_time', '=', False),
                    ('act_over_time', '=', 0.0)
                ], limit=1000)
                
                print(f"Found {len(attendances)} attendance records to recalculate")
                
                recalculated = 0
                errors = 0
                
                for att in attendances:
                    try:
                        # Get shift info
                        if not hasattr(att, 'match_shift') or not att.match_shift:
                            print(f"  ⚠️ Skip {att.id}: No shift")
                            continue
                        
                        shift = att.match_shift
                        if not shift.hr_shift:
                            print(f"  ⚠️ Skip {att.id}: No hr_shift")
                            continue
                        
                        # Get check in/out times
                        checkin = att.check_in
                        checkout = att.check_out
                        
                        # Call calculate_delay_diff_overtime
                        # Note: This requires access to the method from zk.machine
                        # We need to get any zk.machine record to call the method
                        machines = env['zk.machine'].search([], limit=1)
                        if not machines:
                            print("  ❌ No ZK Machine found in database")
                            break
                        
                        machine = machines[0]
                        delay, diff, overtime = machine.calculate_delay_diff_overtime(
                            shift, checkin, checkout, shift.hr_shift
                        )
                        
                        # Update the attendance record
                        att.write({
                            'act_delay_time': delay,
                            'act_diff_time': diff,
                            'act_over_time': overtime,
                        })
                        
                        recalculated += 1
                        if recalculated % 10 == 0:
                            print(f"  ✅ Recalculated {recalculated} records...")
                            cr.commit()  # Commit every 10 records
                        
                    except Exception as e:
                        errors += 1
                        print(f"  ❌ Error processing attendance {att.id}: {e}")
                        continue
                
                # Final commit
                cr.commit()
                
                print(f"\n{'='*60}")
                print(f"✅ Recalculation complete!")
                print(f"  Total processed: {recalculated}")
                print(f"  Errors: {errors}")
                print(f"{'='*60}")
                
                return recalculated, errors
    
    if __name__ == '__main__':
        import argparse
        parser = argparse.ArgumentParser(description='Recalculate attendance delay/diff/overtime')
        parser.add_argument('--database', default='odoo16', help='Database name')
        args = parser.parse_args()
        
        recalculate_attendance(args.database)
        
except ImportError as e:
    print(f"❌ Error: Cannot import Odoo: {e}")
    print("\nThis script must be run on the Odoo server with Odoo installed.")
    print("Usage:")
    print("  python3 recalculate_attendance.py --database odoo16")
    sys.exit(1)
