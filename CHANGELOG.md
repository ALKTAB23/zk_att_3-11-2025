# Changelog - سجل التغييرات

## Version 16.0.0.3 (2025-11-03)

### 🎉 New Features - ميزات جديدة

#### Device Zones (مناطق الأجهزة)
- **Added Device Zone model** for organizing biometric devices by location
- **Automatic timezone synchronization** from zone to device
- **Pre-configured zones** for 10 MENA region locations
- **Comprehensive documentation** in English and Arabic

**Benefits:**
- ✅ No manual timezone configuration needed
- ✅ Easy multi-location device management
- ✅ Better organization by office/branch/region
- ✅ Audit trail for device locations

**Files Added:**
- `models/zk_machine.py`: ZkDeviceZone model
- `views/zk_machine_view.xml`: Zone views and menu items
- `data/zk_device_zones.xml`: Pre-configured zones
- `security/ir.model.access.csv`: Zone access rights
- `ZONES_GUIDE.md`: Bilingual user guide
- `ZONES_QUICK_START_AR.md`: Arabic quick start guide

### 🐛 Bug Fixes - إصلاحات الأخطاء

#### Timezone Display Issue (مشكلة عرض التوقيت)
- **Fixed incorrect timestamp display** where device time (e.g., 9:50 AM) was showing differently in Odoo
- **Implemented proper timezone conversion** from device local time to UTC for database storage
- **Added comprehensive logging** for timezone conversion tracking

**Technical Details:**
- Convert device local time to UTC using proper timezone localization
- Use `pytz.timezone().localize()` for local time
- Convert to UTC with `astimezone(pytz.UTC)` before database storage
- Error handling for timezone conversion failures

**Fixed in commits:**
- `43e7c49`: Initial timezone conversion implementation
- `5749a9a`: Critical fix for using converted timestamp instead of original

#### Time Constraint Removal (إزالة القيد الزمني)
- **Removed shift time constraint** that was preventing display of attendance records outside shift hours
- **All attendance records now display** regardless of shift times
- Attendance records are matched to shifts but displayed even if outside shift hours

**Modified:**
- `models/zk_machine.py` line 202: Removed time range condition in `get_match_shift()`

#### Date Range Filtering (تحسين تصفية نطاق التاريخ)
- **Enhanced date range selection** to support custom periods (e.g., 3 months)
- **Added detailed logging** for debugging date range and record count
- **Verified no 40-day limit** in attendance fetching code

### 🔧 Technical Improvements - تحسينات تقنية

#### Logging Enhancements
- Added Arabic and English logging messages
- Detailed timezone conversion logs
- Date range and record count logs
- Device connection status logs

#### Code Quality
- Better error handling for timezone conversions
- Proper timezone-aware datetime processing
- Consistent use of converted timestamps throughout the code

### 📝 Documentation - التوثيق

#### New Documentation Files
1. **ZONES_GUIDE.md**
   - Comprehensive bilingual guide (English/Arabic)
   - Step-by-step setup instructions
   - Pre-configured zones reference
   - Benefits and use cases

2. **ZONES_QUICK_START_AR.md**
   - Quick start guide in Arabic
   - Practical examples
   - Troubleshooting section
   - Before/after comparison

3. **CHANGELOG.md** (this file)
   - Complete change history
   - Version tracking
   - Feature documentation

### 🗄️ Database Changes - تغييرات قاعدة البيانات

#### New Models
- `zk.device.zone`: Device zones/locations model

#### Modified Models
- `zk.machine`: Added `zone_id` field (Many2one to zk.device.zone)

#### New Security Rules
- `access_zk_device_zone_user`: Read/Write/Create/Unlink access for Attendance Users

### 📦 Module Updates - تحديثات الموديول

#### Manifest Changes
- Version updated to 16.0.0.3 (implied)
- Added `data/zk_device_zones.xml` to data files list

#### Dependencies
- No new dependencies added
- Continues to use: `base_setup`, `hr_attendance`, `pytz`

---

## Version 16.0.0.2 (Previous)

### Features
- Initial ZK biometric device integration
- Attendance download and synchronization
- Shift matching logic
- Check-in/Check-out processing
- Manual and automatic data download
- Scheduler configuration

---

## Migration Guide - دليل الترقية

### From 16.0.0.2 to 16.0.0.3

#### Steps:
1. **Backup your database** before upgrading
2. **Stop Odoo service**
3. **Replace module files** with new version
4. **Restart Odoo service**
5. **Update the module**:
   ```
   Apps > Search "Hemfa - HRMS Biometric" > Upgrade
   ```

#### After Upgrade:
1. **Check new menu**: Attendances > Biometric Manager > Device Zones
2. **Pre-configured zones** will be automatically created
3. **Optional**: Link existing devices to zones for automatic timezone management

#### Data Migration:
- ✅ No data loss
- ✅ Existing devices continue to work
- ✅ No changes to attendance records
- ✅ Zone assignment is optional

---

## Known Issues - المشاكل المعروفة

### None at this time
No known issues in version 16.0.0.3

---

## Upcoming Features - الميزات القادمة

### Planned for Future Versions
- Device status monitoring
- Real-time attendance notifications
- Advanced reporting by zone
- Bulk device configuration
- Device health checks

---

## Credits - شكر وتقدير

**Original Module:**
- Cybrosys Technologies
- Mostafa Shokiel
- Open HRMS

**Version 16.0.0.3 Enhancements:**
- Timezone conversion fixes
- Device Zones feature
- Documentation improvements

---

## Support - الدعم

For issues, questions, or feature requests:
1. Check documentation: `ZONES_GUIDE.md` and `ZONES_QUICK_START_AR.md`
2. Review this changelog
3. Contact your system administrator

---

## License - الترخيص

LGPL v3 (GNU Lesser General Public License)

---

**Last Updated:** 2025-11-03
**Module Version:** 16.0.0.3
**Odoo Version:** 16.0
