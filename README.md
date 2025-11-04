# Hemfa - HRMS Biometric Device Integration (Enhanced)

![Version](https://img.shields.io/badge/version-16.0.0.3-blue.svg)
![Odoo](https://img.shields.io/badge/odoo-16.0-purple.svg)
![License](https://img.shields.io/badge/license-LGPL--3-green.svg)

Enhanced ZK Biometric Device integration for Odoo 16 with advanced timezone handling and device zone management.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [What's New in v16.0.0.3](#whats-new-in-v16003)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Device Zones](#device-zones)
- [Troubleshooting](#troubleshooting)
- [Documentation](#documentation)
- [Credits](#credits)
- [License](#license)

---

## 🎯 Overview

This module integrates Odoo 16 with ZKTeco biometric devices (tested with SpeedFace-V4L and similar models) for automatic attendance tracking. Enhanced with proper timezone conversion and device zone management for multi-location deployments.

### Supported Devices
- ZKTeco SpeedFace-V4L
- ZKTeco uFace 202
- Other ZKTeco devices with similar protocol

---

## ✨ Features

### Core Features
- ✅ Real-time attendance data download from biometric devices
- ✅ Automatic employee attendance record creation
- ✅ Configurable check-in/check-out modes
- ✅ Shift matching and overtime calculation
- ✅ Manual and scheduled attendance synchronization
- ✅ Date range filtering for attendance retrieval

### Enhanced Features (v16.0.0.3)
- 🎉 **Device Zones**: Organize devices by location with automatic timezone sync
- 🔧 **Fixed Timezone Handling**: Device time now displays correctly in Odoo
- 📊 **Enhanced Logging**: Detailed Arabic/English logs for debugging
- 🌍 **Pre-configured MENA Zones**: 10 ready-to-use zones for Middle East & North Africa

---

## 🆕 What's New in v16.0.0.3

### New Features
1. **Device Zones Management**
   - Organize devices by office/branch/region
   - Automatic timezone synchronization from zone to device
   - Pre-configured zones for Libya, Egypt, Saudi Arabia, UAE, Kuwait, Qatar, Jordan, Lebanon

2. **Timezone Conversion Fix**
   - Device local time properly converts to UTC for database storage
   - Odoo displays time correctly based on user timezone
   - Example: Device shows 9:50 AM → Odoo shows 9:50 AM ✓

3. **Time Constraint Removal**
   - All attendance records display regardless of shift times
   - Better visibility of early/late attendance

4. **Enhanced Documentation**
   - Comprehensive bilingual guides (English/Arabic)
   - Quick start guide in Arabic
   - Detailed changelog and migration guide

See [CHANGELOG.md](CHANGELOG.md) for complete details.

---

## 📦 Installation

### Requirements
- Odoo 16.0
- Python 3.8+
- `pyzk` library for ZK device communication
- `pytz` for timezone handling

### Steps

1. **Install Python Dependencies**
   ```bash
   pip install pyzk pytz
   ```

2. **Copy Module to Addons**
   ```bash
   cp -r oh_hr_zk_attendance /path/to/odoo/addons/
   ```

3. **Update Apps List**
   - Login to Odoo
   - Navigate to Apps
   - Click "Update Apps List"

4. **Install Module**
   - Search for "Hemfa - HRMS Biometric"
   - Click "Install"

5. **Verify Installation**
   - Check menu: Attendances > Biometric Manager
   - Should see: Device Configuration, Device Zones, ZK Reading Category

---

## ⚙️ Configuration

### 1. Configure Device

Navigate to: **Attendances > Biometric Manager > Device Configuration**

**Required Settings:**
- **Machine IP**: IP address of the biometric device
- **Port No**: Device port (usually 4370)
- **Device Zone**: Select or create a zone (optional but recommended)
- **Timezone**: Auto-filled from zone, or select manually
- **Working Address**: Office location (optional)

**Attendance Settings:**
- **Log By**: 
  - Check in and Check out (separate punch types)
  - First and Last (first punch = check in, last = check out)
- **Check In Key**: Punch type code for check-in (default: 0)
- **Check Out Key**: Punch type code for check-out (default: 1)

**Data Fetch Settings:**
- **Fetch All Data**: Download all attendance records
- **Fetch within Range**: Download records within date range
  - Set From Date and To Date

**Scheduler Settings:**
- Configure automatic download interval
- Set next scheduled download time
- Enable/disable scheduler

### 2. Configure Device Zone (Recommended)

Navigate to: **Attendances > Biometric Manager > Device Zones**

**For New Zone:**
1. Click "Create"
2. Enter Zone Name (e.g., "Libya - Tripoli Office")
3. Enter Zone Code (e.g., "LY-TPL")
4. Select Timezone (e.g., "Africa/Tripoli")
5. Add description (optional)
6. Save

**Link Device to Zone:**
1. Open device configuration
2. Select zone in "Device Zone" field
3. Timezone will auto-sync!
4. Save

### 3. Link Employees to Device

Navigate to: **Employees > [Employee] > HR Settings**

In "Attendance Devices" section:
1. Add device (Machine IP)
2. Enter Device ID (employee's ID in the biometric device)
3. Save

---

## 🚀 Usage

### Manual Attendance Download

1. Navigate to device configuration
2. Click "Download Data" button
3. Confirm action
4. Wait for data synchronization
5. Check logs for status

### Automatic Attendance Download

1. Configure scheduler in device settings
2. Set interval (e.g., every 1 hour)
3. Set next call time
4. Enable scheduler
5. System will automatically download attendance

### View Attendance Records

Navigate to: **Attendances > Biometric Manager > Attendance**

View:
- Employee name
- Check-in and check-out times
- Matched shift
- Overtime hours
- Early checkout
- Delay time

### Clear Device Data

**⚠️ Warning**: This will delete all attendance data from the device!

1. Navigate to device configuration
2. Click "Clear Data" button
3. Confirm action (cannot be undone)

---

## 🌍 Device Zones

### Why Use Zones?

**Benefits:**
- 📍 Organize devices by location
- ⏰ Automatic timezone configuration
- 🎯 Easy multi-location management
- 📊 Better reporting by location

### Pre-configured Zones

| Zone | Location | Timezone | UTC Offset |
|------|----------|----------|------------|
| LY-TPL | Libya - Tripoli | Africa/Tripoli | +2 |
| EG-CAI | Egypt - Cairo | Africa/Cairo | +2 |
| SA-RYD | Saudi Arabia - Riyadh | Asia/Riyadh | +3 |
| SA-JED | Saudi Arabia - Jeddah | Asia/Riyadh | +3 |
| AE-DXB | UAE - Dubai | Asia/Dubai | +4 |
| AE-AUH | UAE - Abu Dhabi | Asia/Dubai | +4 |
| KW-KWI | Kuwait | Asia/Kuwait | +3 |
| QA-DOH | Qatar - Doha | Asia/Qatar | +3 |
| JO-AMM | Jordan - Amman | Asia/Amman | +2/+3 |
| LB-BEY | Lebanon - Beirut | Asia/Beirut | +2/+3 |

### Quick Start Guide

See [ZONES_QUICK_START_AR.md](ZONES_QUICK_START_AR.md) for detailed Arabic guide.

See [oh_hr_zk_attendance/ZONES_GUIDE.md](oh_hr_zk_attendance/ZONES_GUIDE.md) for comprehensive bilingual guide.

---

## 🔧 Troubleshooting

### Device Connection Issues

**Problem**: Cannot connect to device

**Solutions:**
1. Check device IP address is correct
2. Verify port number (usually 4370)
3. Ensure device is on same network
4. Check firewall settings
5. Test ping to device IP

### Timezone Display Issues

**Problem**: Device shows 9:50 AM but Odoo shows different time

**Solutions:**
1. ✅ **Use Device Zones** (recommended):
   - Create zone with correct timezone
   - Link device to zone
   - Timezone auto-syncs

2. Manual configuration:
   - Open device configuration
   - Set correct timezone manually
   - Save and re-download attendance

3. Check user timezone:
   - User preferences should match location
   - System timezone should be UTC

### No Attendance Records

**Problem**: Download succeeds but no records appear

**Solutions:**
1. Check date range settings (if using range mode)
2. Verify employee is linked to device with correct Device ID
3. Check device has attendance data
4. Review logs for errors
5. Ensure attendance records match shift times (or time constraints are removed)

### Duplicate Records

**Problem**: Same attendance appears multiple times

**Solutions:**
1. Check "Duplicate Punch Period" in device attendance settings
2. Avoid downloading same date range multiple times
3. System should automatically skip duplicates

---

## 📚 Documentation

### Main Documentation
- [README.md](README.md) - This file
- [CHANGELOG.md](CHANGELOG.md) - Version history and changes

### Zone Documentation
- [ZONES_GUIDE.md](oh_hr_zk_attendance/ZONES_GUIDE.md) - Comprehensive bilingual guide
- [ZONES_QUICK_START_AR.md](ZONES_QUICK_START_AR.md) - Arabic quick start

### Technical Documentation
- Module code is documented with inline comments
- See `models/zk_machine.py` for main logic
- See `models/zk/base.py` for device communication

---

## 👥 Credits

### Original Module
- **Developer**: Cybrosys Technologies
- **Contributors**: Mostafa Shokiel, Open HRMS
- **Website**: http://www.openhrms.com

### Version 16.0.0.3 Enhancements
- Timezone conversion fixes
- Device Zones feature
- Enhanced documentation
- Arabic localization improvements

---

## 📄 License

This module is licensed under **LGPL v3** (GNU Lesser General Public License).

You can modify it under the terms of the GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

## 📞 Support

For issues, questions, or feature requests:

1. Review documentation (README, CHANGELOG, guides)
2. Check troubleshooting section
3. Review logs in Odoo (Settings > Technical > Logging)
4. Contact your system administrator

---

## 🎯 Roadmap

### Planned Features
- Device status monitoring dashboard
- Real-time attendance notifications
- Advanced reporting by zone/location
- Bulk device configuration tools
- Device health checks and diagnostics
- Mobile app integration

---

## 📊 Statistics

- **Supported Devices**: ZKTeco SpeedFace, uFace series
- **Languages**: English, Arabic
- **Timezones**: All IANA timezones supported
- **Pre-configured Zones**: 10 MENA region zones
- **Odoo Version**: 16.0
- **Module Version**: 16.0.0.3

---

**Last Updated**: 2025-11-03

**Module**: Hemfa - HRMS Biometric Device Integration

**Version**: 16.0.0.3

**Odoo**: 16.0

---

Made with ❤️ for better workforce management
