# Device Zones Guide - دليل مناطق الأجهزة

## English

### What are Device Zones?

Device Zones in ZK Attendance module help you organize your biometric devices by geographical location and automatically manage timezone settings. This feature is inspired by ZK BioTime's zone functionality.

### Key Features

1. **Geographic Organization**: Group devices by location (offices, branches, countries)
2. **Automatic Timezone Sync**: When you assign a zone to a device, the device's timezone is automatically set
3. **Centralized Management**: Manage all devices in a zone from one place
4. **Multi-location Support**: Perfect for companies with multiple offices across different timezones

### How to Use

#### 1. Create a Device Zone

Navigate to: **Attendances > Biometric Manager > Device Zones**

1. Click "Create"
2. Enter Zone Name (e.g., "Libya - Tripoli Office")
3. Enter Zone Code (e.g., "LY-TPL")
4. Select Timezone (e.g., "Africa/Tripoli")
5. Add description (optional)
6. Save

#### 2. Assign Zone to Device

Navigate to: **Attendances > Biometric Manager > Device Configuration**

1. Open an existing device or create a new one
2. In the "Device Zone" field, select the appropriate zone
3. **The timezone will be automatically set from the zone!**
4. Save

#### 3. View Devices in Zone

1. Open any zone record
2. Go to "Devices in Zone" tab
3. You'll see all devices assigned to this zone

### Pre-configured Zones

The module includes demo zones for common Middle East and North Africa regions:

| Zone Code | Location | Timezone | UTC Offset |
|-----------|----------|----------|------------|
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

### Benefits

✅ **No Manual Timezone Configuration**: Timezone is set automatically when you select a zone

✅ **Consistent Time Handling**: All devices in the same location use the same timezone

✅ **Easy Management**: Update timezone for all devices in a zone at once

✅ **Better Organization**: Group devices by office, branch, or region

✅ **Audit Trail**: Track which devices belong to which locations

---

## العربية

### ما هي مناطق الأجهزة؟

مناطق الأجهزة في موديول ZK Attendance تساعدك على تنظيم أجهزة البصمة حسب الموقع الجغرافي وإدارة إعدادات التوقيت تلقائياً. هذه الميزة مستوحاة من خاصية Zone في نظام ZK BioTime.

### المميزات الرئيسية

1. **التنظيم الجغرافي**: تجميع الأجهزة حسب الموقع (المكاتب، الفروع، الدول)
2. **مزامنة التوقيت التلقائية**: عند تعيين منطقة للجهاز، يتم ضبط التوقيت تلقائياً
3. **الإدارة المركزية**: إدارة جميع الأجهزة في المنطقة من مكان واحد
4. **دعم المواقع المتعددة**: مثالي للشركات التي لديها مكاتب متعددة في مناطق زمنية مختلفة

### كيفية الاستخدام

#### 1. إنشاء منطقة جهاز

الانتقال إلى: **Attendances > Biometric Manager > Device Zones**

1. اضغط "Create"
2. أدخل اسم المنطقة (مثال: "ليبيا - مكتب طرابلس")
3. أدخل كود المنطقة (مثال: "LY-TPL")
4. اختر المنطقة الزمنية (مثال: "Africa/Tripoli")
5. أضف وصف (اختياري)
6. احفظ

#### 2. تعيين منطقة للجهاز

الانتقال إلى: **Attendances > Biometric Manager > Device Configuration**

1. افتح جهاز موجود أو أنشئ جديد
2. في حقل "Device Zone"، اختر المنطقة المناسبة
3. **سيتم ضبط التوقيت تلقائياً من المنطقة!**
4. احفظ

#### 3. عرض الأجهزة في المنطقة

1. افتح أي سجل منطقة
2. اذهب إلى تبويب "Devices in Zone"
3. سترى جميع الأجهزة المعينة لهذه المنطقة

### المناطق المُعدة مسبقاً

الموديول يتضمن مناطق تجريبية للمناطق الشائعة في الشرق الأوسط وشمال أفريقيا:

| كود المنطقة | الموقع | المنطقة الزمنية | فرق التوقيت |
|-------------|---------|----------------|-------------|
| LY-TPL | ليبيا - طرابلس | Africa/Tripoli | +2 |
| EG-CAI | مصر - القاهرة | Africa/Cairo | +2 |
| SA-RYD | السعودية - الرياض | Asia/Riyadh | +3 |
| SA-JED | السعودية - جدة | Asia/Riyadh | +3 |
| AE-DXB | الإمارات - دبي | Asia/Dubai | +4 |
| AE-AUH | الإمارات - أبوظبي | Asia/Dubai | +4 |
| KW-KWI | الكويت | Asia/Kuwait | +3 |
| QA-DOH | قطر - الدوحة | Asia/Qatar | +3 |
| JO-AMM | الأردن - عمان | Asia/Amman | +2/+3 |
| LB-BEY | لبنان - بيروت | Asia/Beirut | +2/+3 |

### الفوائد

✅ **لا حاجة لضبط التوقيت يدوياً**: يتم ضبط التوقيت تلقائياً عند اختيار المنطقة

✅ **معالجة وقت متسقة**: جميع الأجهزة في نفس الموقع تستخدم نفس التوقيت

✅ **إدارة سهلة**: تحديث التوقيت لجميع الأجهزة في المنطقة دفعة واحدة

✅ **تنظيم أفضل**: تجميع الأجهزة حسب المكتب، الفرع، أو المنطقة

✅ **سجل المراجعة**: تتبع الأجهزة التي تنتمي لأي موقع

### مثال عملي

إذا كان لديك:
- مكتب رئيسي في طرابلس
- فرع في بنغازي
- فرع في الرياض

**بدون Zones:**
- تحتاج لضبط التوقيت لكل جهاز يدوياً
- صعوبة في معرفة أي جهاز في أي موقع

**مع Zones:**
1. أنشئ منطقة "ليبيا - طرابلس" (Africa/Tripoli)
2. أنشئ منطقة "ليبيا - بنغازي" (Africa/Tripoli)
3. أنشئ منطقة "السعودية - الرياض" (Asia/Riyadh)
4. عند إضافة جهاز جديد، اختر المنطقة فقط!
5. التوقيت يُضبط تلقائياً ✓

### ملاحظات مهمة

⚠️ **عند تغيير timezone المنطقة**: لن يتم تحديث الأجهزة الموجودة تلقائياً. يجب عليك:
1. فتح كل جهاز
2. إعادة اختيار المنطقة (أو تحديث حقل Timezone يدوياً)
3. حفظ

💡 **نصيحة**: استخدم Zone Code قصيرة وواضحة لسهولة التعرف على الأجهزة في التقارير
