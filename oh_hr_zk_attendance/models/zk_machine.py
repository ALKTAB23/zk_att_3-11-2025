# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import pytz
#import os
#3import sys
#CWD = os.path.dirname(os.path.realpath(__file__))
#ROOT_DIR = os.path.dirname(CWD)
#sys.path.append(ROOT_DIR)

from odoo.addons.oh_hr_zk_attendance.models.zk.base import ZK, const

import datetime
import logging
import binascii
import calendar
import logging
from struct import unpack
from odoo import api, fields, models,_
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from odoo.addons.base.models.res_partner import _tz_get
class HrAttendance(models.Model):
    _inherit = 'hr.attendance'
    is_process=fields.Boolean('is_process',default=False)
    @api.constrains('check_in', 'check_out')
    def _check_validity_check_in_check_out(self):
        """ verifies if check_in is earlier than check_out. """
        for attendance in self:
            if attendance.check_in and attendance.check_out:
                
                if attendance.check_out < attendance.check_in:
                    checkin=attendance.check_in
                    checkout=attendance.check_out
                    attendance.check_out=checkin
                    attendance.check_in=checkout
                    # raise ValidationError(_('"Check Out" time cannot be earlier than "Check In" time.'))
    @api.constrains('check_in', 'check_out', 'employee_id')
    def _check_validity(self):
        pass
class HrAtt_types_read(models.Model):
    _name = 'attendance_types_readings'
    code=fields.Char('Code',required=True)
    name=fields.Char('Type Name',required=True)

class ZkMachine(models.Model):
    _name = 'zk.machine'

    name = fields.Char(string='Machine IP', required=True)
    port_no = fields.Integer(string='Port No', required=True)
    address_id = fields.Many2one('res.partner', string='Working Address')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id.id)
    log_by_check_in_check_out=fields.Selection([ ('check_in_out','Log by Check in and Check out'),
                                                 ('check_first_last','Log by First and Last')],string='Log By', default='check_first_last')
    checkin_read_key=fields.Integer('Check In Key',default='0')
    checkout_read_key=fields.Integer('Check Out Key',default='1')
    fetch_data_setting=fields.Selection([ ('all','Fetch All Data'),
                                          ('range','Fetch within Range')],string='Fetch Setting', default='all')
    from_date=fields.Date(string="From Date")
    to_date=fields.Date(string="To Date")
    read_tz=fields.Selection(
        _tz_get, string='Timezone', required=True,
        default=lambda self: self._context.get('tz') or self.env.user.tz or 'UTC',
        help="This field is used in order to define in which timezone the resources will work.")
    att_type=fields.Many2one('attendance_types_conf',string='Attendance Type Configuration')
    def __get_sc(self):
    	d=self.env['ir.cron'].search([('name','=','Download Data')])
    	return d[0].id
    schedule_action=fields.Many2one('ir.cron',string='Scheduler',default=__get_sc,readonly=True)
    interval_n=fields.Integer(string='Interval Every',related='schedule_action.interval_number')
    lastcall=fields.Datetime(string="Last Call",related='schedule_action.lastcall')
    nextcall=fields.Datetime(string="Next Call",related='schedule_action.nextcall')
    is_active=fields.Boolean(string="Active",related='schedule_action.active')
    set_nextcall=fields.Datetime(string="Set Next Call",)
    interval_set=fields.Integer(string='Interval Every')
    interval_t_set = fields.Selection([('minutes', 'Minutes'),
                                      ('hours', 'Hours'),
                                      ('days', 'Days'),
                                      ('weeks', 'Weeks'),
                                      ('months', 'Months')], string='Interval Unit',default='hours' )
    interval_t = fields.Selection([('minutes', 'Minutes'),
                                      ('hours', 'Hours'),
                                      ('days', 'Days'),
                                      ('weeks', 'Weeks'),
                                      ('months', 'Months')], string='Interval Unit', related="schedule_action.interval_type")
    def enable_dis_sched(self):
        if self.schedule_action:
            if self.schedule_action.active:
                self.schedule_action.active=False
            else:
                self.schedule_action.active=True

    def write(self, vals):
        if 'to_date' in vals:
            from_d=vals['from_date']
            fromdate=datetime.strptime(vals['from_date'],'%Y-%m-%d').date()
            todate=datetime.strptime(vals['to_date'],'%Y-%m-%d').date()
            days=(todate-fromdate).days
            if days>40:
                raise ValidationError('The different days must be less than 40 days!')

        return super(ZkMachine, self).write(vals)
    def update_interval(self):
        self.schedule_action.interval_number=self.interval_set
        self.schedule_action.nextcall=self.set_nextcall
        if self.interval_t_set:
            self.schedule_action.interval_type=self.interval_t_set
    def days_between(self,d1, d2):
        return abs((d2 - d1).days)
    def device_connect(self, zk):
        try:
            conn = zk.connect()
            return conn
        except:
            return False

    def clear_attendance(self):
        for info in self:
            try:
                machine_ip = info.name
                zk_port = info.port_no
                timeout = 30
                self._cr.execute("""delete from zk_machine_attendance""")
                
            except:
                raise ValidationError(
                    'Unable to clear Attendance log. Are you sure attendance device is connected & record is not empty.')


    @api.model
    def cron_download(self):
        machines = self.env['zk.machine'].search([])
        for machine in machines:
            machine.download_attendance()

    
    def get_match_shift(self,current_time, current_employee):
        emp_rec=self.env['hr.contract'].get_employee_contract(self.env['hr.employee'].browse(current_employee))
        if emp_rec:
            attend_date_now=datetime.strptime(current_time,'%Y-%m-%d %H:%M:%S')
            curr_time=attend_date_now
            attend_date_now=datetime(attend_date_now.year,attend_date_now.month,attend_date_now.day)
            wshedule=self.env['attendance.sheet'].get_schedule(emp_rec,curr_time)
            if wshedule:
                tz = pytz.timezone(wshedule.tz)
                curr_time=pytz.utc.localize(curr_time).astimezone(tz).replace(tzinfo=None)
                diff_no=0
                shift_index=0
                
                if emp_rec:
                    schedules=emp_rec[0].shift_schedule
                    match_schedules=schedules.search([('start_date','<=',str(attend_date_now)),('active','=',True),('rel_hr_schedule','=',emp_rec[0].id)])
                    active_schedule_id=False
                    sft_start_date=False
                    for sc in match_schedules:
                        if sc.end_date:
                            sc_end_date=datetime(sc.end_date.year,sc.end_date.month,sc.end_date.day)
                            if attend_date_now.date() <= sc_end_date.date():
                                sft_start_date=sc.start_date
                                diff_no=self.days_between(sft_start_date,attend_date_now.date())
                                active_schedule_id=sc.hr_shift
                        else:
                            sft_start_date=sc.start_date
                            diff_no=self.days_between(sft_start_date,attend_date_now.date())
                            active_schedule_id=sc.hr_shift
                    
                    shift_index=diff_no
                    if active_schedule_id:
                        shifts_len=len(active_schedule_id.shifts_config_ids)
                        shift_index=diff_no
                        for n in range(diff_no):
                            if shift_index<shifts_len:
                                break
                            shift_index=shift_index-shifts_len
                    match_shift=False
                    if active_schedule_id:
                        if active_schedule_id.recurring_sequence=='weekly':
                            day=attend_date_now.weekday()
                            
                            for r in active_schedule_id.shifts_config_ids.sorted(lambda o: o.sequence):
                                
                                if str(r.dayofweek)==str(day) and r.week_type==active_schedule_id.shifts_config_ids.sorted(lambda o: o.sequence)[shift_index].week_type:
                                    # تم إلغاء شرط الوقت - يقبل كل البصمات بغض النظر عن وقت انتهاء الوردية
                                    match_shift=r
                                    break                    
                        else:#daily
                            match_shift=active_schedule_id.shifts_config_ids.sorted(lambda o: o.sequence)[shift_index]
                    return match_shift
        return False
    def get_time_from_float(self, float_type):
        str_off_time = str(float_type)
        official_hour = str_off_time.split('.')[0]
        official_minute = int(round(round(float("0." + str_off_time.split('.')[1]),6)*60))
        if official_minute>=60:
            official_minute=0
        str_off_time = official_hour + ":" + str(official_minute)
        str_off_time = datetime.strptime(str_off_time, "%H:%M").time()
        return str_off_time
    def calculate_delay_diff_overtime(self,match_shift_computed,checkin,checkout, match_shift=False):
        checkin_config_hour=0
        checkout_config_hour=0
        self.env['resource.calendar'].update_shifts()
        # Calculate delay, diff and overtime
        if match_shift_computed:
            shfit_rec=match_shift_computed.hr_shift
            if match_shift:
                shfit_rec=match_shift
            overtime=0.0
            delay=0.0
            diff=0.0
            permit_check_in=match_shift_computed.att_policy_id.permit_check_in
            permit_check_out=match_shift_computed.att_policy_id.permit_check_out
            tz = pytz.timezone(match_shift_computed.schedule_id.tz)
            checkin=pytz.utc.localize(checkin).astimezone(tz).replace(tzinfo=None)+timedelta(hours=checkin_config_hour)
            if checkout:
                checkout=pytz.utc.localize(checkout).astimezone(tz).replace(tzinfo=None)-timedelta(hours=checkout_config_hour)
            ex_hour_from=str(self.get_time_from_float(shfit_rec.hour_from))
            chour=int(ex_hour_from.split(":")[0])
            cminute=int(ex_hour_from.split(":")[1])
            expect_check_in=datetime(checkin.year,checkin.month,checkin.day,chour,cminute, 0)
            checkin_utc=checkin
            check_in_as_time=datetime(checkin_utc.year,checkin_utc.month,checkin_utc.day,checkin_utc.hour,checkin_utc.minute, 0)
            checkin_time_float=self._get_float_from_time(check_in_as_time)
            # calc delay by subtract checkin - expected checkin
            ex_hour_to=str(self.get_time_from_float(shfit_rec.hour_to))
            chour=int(ex_hour_to.split(":")[0])
            cminute=int(ex_hour_to.split(":")[1])
            if checkout:
                delay_totalminutes=0
                chin=checkin_time_float
                hf=shfit_rec.hour_from
                if chin>hf:
                    # Calculate delay time of attendance
                    if int(chin)==0:
                        if 24-chin>24-hf:
                            delay_totalminutes=self.subtract_two_times_24h(checkin_time_float,hf)
                    else:
                        delay_totalminutes=self.subtract_two_times_24h(checkin_time_float,hf)
                else:
                    if int(chin)==0:
                        if 24-chin>24-hf:
                            delay_totalminutes=self.subtract_two_times_24h(checkin_time_float,hf)
                if delay_totalminutes>permit_check_in:
                    delay=delay_totalminutes-permit_check_in
                
                checkout_utc=checkout
                

                
                check_out_as_time=datetime(checkout_utc.year,checkout_utc.month,checkout_utc.day,checkout_utc.hour,checkout_utc.minute, 0)
                
                checkout_time_float=self._get_float_from_time(check_out_as_time)
                ## calc overtime by subtract checkout -  checkin
                act_overtime_minutes=self.subtract_two_times_24h(checkout_time_float,checkin_time_float)
                
                expect_work_minutes=self.subtract_two_times_24h(shfit_rec.hour_to,shfit_rec.hour_from)

                
                diff_totalminutes=0
                ht=shfit_rec.hour_to
                co=checkout_time_float
                checkout_utc=checkout-timedelta(hours=checkout_config_hour)
                check_out_as_time=datetime(checkout_utc.year,checkout_utc.month,checkout_utc.day,checkout_utc.hour,checkout_utc.minute, 0)
                checkout_time_float=self._get_float_from_time(check_out_as_time)
                if ht>co:
                    # Calculate Early checkout 
                    if int(ht)==0:
                        if 24-ht>24-co:
                            diff_totalminutes=self.subtract_two_times_24h(shfit_rec.hour_to,checkout_time_float)

                    else:
                        if 24-ht>24-co:
                            diff_totalminutes=self.subtract_two_times_24h(shfit_rec.hour_to,checkout_time_float)
                        else:
                            if ht>co:
                                diff_totalminutes=self.subtract_two_times_24h(shfit_rec.hour_to,checkout_time_float)
                else:
                    if int(ht)==0:
                        if 24-ht>24-co:
                            diff_totalminutes=self.subtract_two_times_24h(shfit_rec.hour_to,checkout_time_float)



                if diff_totalminutes>permit_check_out:
                    diff=diff_totalminutes-permit_check_out

                
                if act_overtime_minutes> expect_work_minutes:
                    overtime=act_overtime_minutes-expect_work_minutes
            return delay, diff, overtime
    def _get_float_from_time(self, time):
        time_type = datetime.strftime(time, "%H:%M:%S")
        signOnP = [int(n) for n in time_type.split(":")]
        signOnH = signOnP[0] + signOnP[1] / 60.0+ signOnP[2]/3600
        return signOnH
    def subtract_two_times_24h(self, time_from,time_to):
        t1=str(self.get_time_from_float(time_from))
        t2=str(self.get_time_from_float(time_to))
        c1hour=int(t1.split(":")[0])
        c1minute=int(t1.split(":")[1])
        c2hour=int(t2.split(":")[0])
        c2minute=int(t2.split(":")[1])
        s_h=c1hour-c2hour
        if c2hour==0:
            s_h=24-s_h 
        s_m=c1minute-c2minute
        if s_h<0:
            s_h+=24
        if s_m <0:
            s_m+=60
            s_h-=1
            if s_h<0:
                s_h=0
        if s_h==24:
            s_h=0
        convert_to_time=datetime(1,1,1,s_h,s_m, 0)
        return self._get_float_from_time(convert_to_time)
    def download_attendance(self):
        """تحميل سجلات الحضور من جهاز البصمة مع معالجة شاملة للأخطاء"""
        _logger = logging.getLogger(__name__)
        _logger.info("=== بدء تحميل سجلات الحضور ===")
        
        zk_attendance = self.env['zk.machine.attendance']
        att_obj = self.env['hr.attendance']
        
        for info in self:
            machine_ip = info.name
            zk_port = info.port_no
            timeout = 50
            
            _logger.info(f"محاولة الاتصال بالجهاز: {machine_ip}:{zk_port}")
            
            # 1. التحقق من تثبيت مكتبة pyzk
            try:
                zk = ZK(machine_ip, port=zk_port, timeout=timeout, password=0, force_udp=False, ommit_ping=False)
            except NameError:
                raise UserError(_("مكتبة Pyzk غير مثبتة. يرجى تثبيتها باستخدام: pip3 install pyzk"))
            except Exception as e:
                _logger.error(f"خطأ في إنشاء كائن ZK: {str(e)}")
                raise UserError(_(f"خطأ في تهيئة الاتصال بالجهاز: {str(e)}"))
            
            # 2. محاولة الاتصال بالجهاز
            conn = None
            try:
                conn = zk.connect()
                _logger.info("✓ نجح الاتصال بالجهاز")
            except Exception as e:
                _logger.error(f"فشل الاتصال بالجهاز: {str(e)}")
                raise UserError(_(f"فشل الاتصال بجهاز البصمة {machine_ip}:{zk_port}\n"
                                 f"تحقق من:\n"
                                 f"1. عنوان IP صحيح\n"
                                 f"2. المنفذ Port صحيح (عادة 4370)\n"
                                 f"3. الجهاز متصل بالشبكة\n"
                                 f"4. لا يوجد Firewall يمنع الاتصال\n"
                                 f"تفاصيل الخطأ: {str(e)}"))
            
            if not conn:
                raise UserError(_(f"لا يمكن الاتصال بالجهاز {machine_ip}. تحقق من الإعدادات."))
            
            # 3. تعطيل الجهاز مؤقتاً أثناء القراءة
            try:
                conn.disable_device()
                _logger.info("✓ تم تعطيل الجهاز للقراءة")
            except Exception as e:
                _logger.error(f"فشل تعطيل الجهاز: {str(e)}")
            
            if conn:
                # conn.disable_device() #Device Cannot be used during this time.
                # 4. قراءة قائمة المستخدمين من الجهاز
                user = False
                try:
                    user = conn.get_users()
                    _logger.info(f"✓ تم قراءة {len(user) if user else 0} مستخدم من الجهاز")
                except Exception as e:
                    _logger.error(f"فشل قراءة المستخدمين: {str(e)}")
                    user = False
                
                # 5. قراءة سجلات الحضور من الجهاز
                attendance = False
                try:
                    if self.fetch_data_setting == 'range':
                        if self.to_date:
                            _logger.info(f"قراءة السجلات من {self.from_date} إلى {self.to_date}")
                            _logger.info(f"إعداد الجلب: fetch_data_setting={self.fetch_data_setting}")
                            attendance = conn.get_attendance(
                                start_date=str(self.from_date),
                                end_date=str(self.to_date),
                                policy='range'
                            )
                        else:
                            _logger.info(f"قراءة السجلات من {self.from_date} فقط (بدون تاريخ نهاية)")
                            attendance = conn.get_attendance()
                    else:
                        _logger.info("قراءة جميع السجلات (policy='all')")
                        attendance = conn.get_attendance(policy='all')
                    
                    # تسجيل نتيجة القراءة بالتفصيل
                    if attendance:
                        _logger.info(f"✓ نجحت القراءة: تم استرجاع {len(attendance)} سجل حضور")
                        if len(attendance) > 0:
                            # عرض أول وآخر سجل للتأكد من النطاق
                            first_record = attendance[0]
                            last_record = attendance[-1]
                            _logger.info(f"  أول سجل: {first_record.timestamp} - {first_record.user_id}")
                            _logger.info(f"  آخر سجل: {last_record.timestamp} - {last_record.user_id}")
                    else:
                        _logger.warning("⚠ لا توجد سجلات حضور جديدة في الجهاز")
                        
                except Exception as e:
                    _logger.error(f"خطأ أثناء قراءة سجلات الحضور: {str(e)}")
                    attendance = False
                
                users_list = []
                for uid in user:
                	users_list.append(uid.user_id)
                # 6. معالجة السجلات المقروءة
                if not attendance:
                    conn.enable_device()
                    raise UserError(_(
                        "لم يتم العثور على سجلات حضور جديدة.\n\n"
                        "الأسباب المحتملة:\n"
                        "1. لا توجد سجلات جديدة في الجهاز منذ آخر مزامنة\n"
                        "2. الموظفين غير مسجلين في النظام\n"
                        "3. خطأ في إعدادات التاريخ (إذا كنت تستخدم نطاق تاريخ محدد)\n\n"
                        f"عدد السجلات المقروءة: {len(attendance) if attendance else 0}\n"
                        f"عدد المستخدمين في الجهاز: {len(user) if user else 0}"
                    ))
                
                if attendance:
                    _logger.info(f"بدء معالجة {len(attendance)} سجل حضور")
                    tz = pytz.timezone(self.read_tz)
                    
                    for each in attendance:
                        # logging.info("att>>>>>"+str(each.punch)+"__"+str(self.checkin_read_key)+"_")
                        if str(each.punch) == str(self.checkin_read_key) or str(each.punch) == str(self.checkout_read_key):
                            # الوقت من الجهاز هو الوقت المحلي مباشرة - لا يحتاج تحويل
                            atten_time = each.timestamp
                            _logger.debug(f"وقت البصمة الأصلي من الجهاز: {atten_time}")
                            if user:
                                # for uid in user:
                                if each.user_id in users_list:
                                    duplicate_atten_ids = zk_attendance.search(
                                        [('device_id', '=', each.user_id), ('punching_time', '=', atten_time),('machine_ip','=',self.id)])
                                    
                                    if duplicate_atten_ids:
                                        continue
                                    else:
                                        employee_device=self.env['hr.employee.devices_ids'].search([('machine_ip','=',self.id),('device_id','=',each.user_id)])
                                        get_user_id=False
                                        if employee_device:
                                            get_user_id=employee_device[0].emp_id
                                        if get_user_id:
                                            c_time = datetime.strptime(str(each.timestamp), '%Y-%m-%d %H:%M:%S')
                                            at_name=""
                                            att_t=self.env['attendance_types_readings'].search([('code','=',str(each.status))])
                                            
                                            if att_t:
                                                at_name=att_t[0].name
                                            # logging.info("att>>>>>2222 Create")
                                            zk_attendance.create({'employee_id': get_user_id.id,
                                                                  'device_id': each.user_id,
                                                                  'machine_ip': self.id,
                                                                  'attendance_typee': at_name,
                                                                  'punch_type': str(each.punch),
                                                                  'punching_time': atten_time,
                                                                  'address_id': info.address_id.id,
                                                                  'punching_day': atten_time,
                                                                  'is_process':False
                                                                  })
                                    # break
                    conn.enable_device()
                    
                    query = """
                                select punching_day 
                                from zk_machine_attendance
                                where is_process=False
                                group by punching_day
                                order by punching_day asc
                    """
                    self._cr.execute(query)
                    current_dates=self.env.cr.fetchall()
                    emp_rec=False
                    for c_date in current_dates:
                        query = """
                                select employee_id 
                                from zk_machine_attendance
                                where is_process=False
                                group by punching_day,employee_id
                                having punching_day='%s'
                        """%(c_date)
                        self._cr.execute(query)
                        current_employees=self.env.cr.fetchall()
                        # logging.info("att>>>>>finish Create")
                        for emp in current_employees:
                            emp_rec=self.env['hr.contract'].search([('employee_id','=',emp[0]),('state','=','open')])
                            if len(emp_rec)>0:
                                for cont in emp_rec:
                                    self.register_attendances(emp,cont,c_date,att_obj,info)

                    _logger.info("=== اكتملت عملية تحميل السجلات بنجاح ===")
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': _('نجح!'),
                            'message': _('تم استيراد {} سجل حضور بنجاح').format(len(attendance)),
                            'type': 'success',
                            'sticky': False,
                        }
                    }
            
            # في حالة عدم وجود اتصال (لن يصل لهنا عادةً)
            conn.enable_device()
            raise UserError(_(
                'فشل الاتصال بجهاز البصمة.\n\n'
                'تحقق من:\n'
                '1. عنوان IP: {}\n'
                '2. المنفذ Port: {}\n'
                '3. الجهاز متصل بالشبكة\n'
                '4. لا يوجد Firewall يمنع الاتصال'
            ).format(machine_ip, zk_port))
    def get_shift_of_requests(self,req_date, emp):
        emp_r=self.env['hr.employee'].browse(emp)
        emp_rec=self.env['hr.contract'].get_employee_contract(emp_r)
        if emp_rec:
            match_shift=False
            req_type=''
            request=False
            for req in emp_rec.shift_schedule2:
                if req.state=='approved':
                    if req.start_date==req_date:
                        if req.request_id.request_type=='change':
                            match_shift=req.hr_shift
                            req_type='change'
                            request=req.id
                        else:
                            if req.request_id.request_type=='compensate_shift':
                                match_shift=req.hr_shift
                                req_type='compensate_shift'
                                pass
            return match_shift,req_type,request
        return False


    def search_and_fill(self,arr,match_shift_computed,shift_id,time,punch_type,logtype):
        if logtype=='check_in_out':
            if not shift_id in arr:
                arr[shift_id]=[{'time':time,'punch_type':punch_type,'shift':shift_id,'shift_rec':match_shift_computed}]
            else:
                if punch_type!='0':
                    arr[shift_id].append({'time':time,'punch_type':punch_type,'shift':shift_id,'shift_rec':match_shift_computed})
        else:
            if not shift_id in arr:
                arr[shift_id]=[{'time':time,'punch_type':punch_type,'shift':shift_id,'shift_rec':match_shift_computed}]
            else:                
                arr[shift_id].append({'time':time,'punch_type':punch_type,'shift':shift_id,'shift_rec':match_shift_computed})
        return arr

    def register_attendances(self,emp,emp_rec,c_date,att_obj,machine_ip):
        emp_r=self.env['hr.employee'].browse(emp[0])
        emp_rec=self.env['hr.contract'].get_employee_contract(emp_r)
        if emp_rec:
            if self.log_by_check_in_check_out=='check_in_out':
                check_in_recs=self.env['zk.machine.attendance'].search([('punching_day','=',str(c_date[0])),
                    ('employee_id','=',emp[0]),('is_process','=',False),
                    ('machine_ip','=',machine_ip.id)],
                    order='punching_time')
                new_att=False
                att_arr={}
                # save_date=False
                match_shift_computed=False
                for rec in check_in_recs:
                    # if rec.punching_time.date()!=save_date:
                    match_shift_computed=self.get_match_shift(str(rec.punching_time),emp[0])
                    # save_date=rec.punching_time.date()

                    if match_shift_computed:
                        att_arr=self.search_and_fill(att_arr,match_shift_computed,match_shift_computed.hr_shift.id,rec.punching_time,rec.punch_type,self.log_by_check_in_check_out)
                    rec.is_process=True
                first=0
                for pkey,rec_shift in att_arr.items():
                    new_att=False
                    delay_totalminutes=0
                    checkin_t=''
                    checkout=''
                    flag=False
                    if first==0:
                        read_r=0
                        for p_rec in rec_shift:
                            read_r=p_rec['punch_type']
                            if str(p_rec['punch_type'])=='0' or str(p_rec['punch_type'])==str(self.checkin_read_key):
                                flag=True
                                break
                        first=1
                    if flag==False:
                        raise ValidationError(_('Invalid Checkin Configuration read %s and configured %s !'%(read_r,self.checkin_read_key)))
                    ins_flag=True
                    for punch_rec in rec_shift:
                        if str(punch_rec['punch_type'])=='0' or str(punch_rec['punch_type'])==str(self.checkin_read_key) and ins_flag:
                            checkin_t=punch_rec['time']
                            ins_flag=False

                            shift_obj=self.env['shift_data'].browse(punch_rec['shift'])
                            
                            new_att=att_obj.create({'employee_id': emp[0],
                                        'check_in': punch_rec['time'],
                                        'match_shift':punch_rec['shift'],
                                        'att_shift_rec':punch_rec['shift_rec'].id,
                                        'expected_check_in':shift_obj.hour_from,
                                        'expected_check_out':shift_obj.hour_to,
                                       # 'linked_request':request,
                                        })
                        else:
                            if new_att:
                                delay=0.0
                                diff=0.0
                                overtime=0.0

                                checkout=punch_rec['time']
                                # checkin_t=check_in_recs[0].punching_time
                                delay,diff,overtime=self.calculate_delay_diff_overtime(punch_rec['shift_rec'],checkin_t,checkout,punch_rec['shift_rec'].hr_shift)
                                
                                new_att.write({ 'check_out': checkout,
                                            'is_process':True,
                                            'act_delay_time':delay,
                                            'act_diff_time':diff,
                                            'act_over_time':overtime,
                                        })

            else: #First check in last checkout
                check_in_recs=self.env['zk.machine.attendance'].search([('punching_day','=',c_date[0]),('employee_id','=',emp[0]),('is_process','=',False),('machine_ip','=',machine_ip.id)],order='punching_time')
                
                new_att=False
                tz=None
                new_att=False
                att_arr={}
                match_shift_computed=False
                for rec in check_in_recs:
                    match_shift_computed=self.get_match_shift(str(rec.punching_time),emp[0])
                    attend_date_now=datetime.strptime(str(rec.punching_time),'%Y-%m-%d %H:%M:%S')
                    
                    if match_shift_computed:
                        att_arr=self.search_and_fill(att_arr,match_shift_computed,match_shift_computed.hr_shift.id,rec.punching_time,rec.punch_type,self.log_by_check_in_check_out)
                    rec.is_process=True
                for key,rec_shift in att_arr.items():
                    new_att=False
                    delay_totalminutes=0

                    if len(rec_shift)>1:
                        i=0
                        psave=False
                        for punch_rec in rec_shift:
                            if i==0:
                                shift_obj=self.env['shift_data'].browse(punch_rec['shift'])
                                new_att=self.env['hr.attendance'].create({'employee_id': emp[0],
                                            'check_in': punch_rec['time'],
                                            'att_shift_rec':punch_rec['shift_rec'].id,
                                            'match_shift':punch_rec['shift'],
                                            'expected_check_in':shift_obj.hour_from,
                                            'expected_check_out':shift_obj.hour_to,
                                            })
                                i+=1
                            else:
                                psave=punch_rec
                                f_time=self._get_float_from_time(punch_rec['time'])
                                if match_shift_computed:
                                    if (shift_obj.hour_to+match_shift_computed.att_policy_id.permit_check_out)<f_time:
                                        break
                        if psave:
                            checkin_float=self._get_float_from_time(new_att.check_in)
                            checkout_float=self._get_float_from_time(psave['time'])
                            delay_totalminutes=self.subtract_two_times_24h(checkout_float,checkin_float)
                            dd=psave['time']-new_att.check_in
                            shift_record2=self.env['attendance.sheet'].browse(psave['shift_rec'])
                            wshedule=self.env['attendance.sheet'].get_schedule(emp_rec,new_att.check_in)
                            avg_hour=0
                            if wshedule:
                                avg_hour=wshedule.hours_per_day
                            hours_per_day=avg_hour
                            delay_totalminutes=hours_per_day-delay_totalminutes

                            totalminutes=(psave['time'] - new_att.check_in).total_seconds() / 60.0
                            checkout=False
                            delay=0.0
                            diff=0.0
                            overtime=0.0
                            if totalminutes>=60:
                                shift_record=self.env['shift_data'].browse(psave['shift'])
                                delay,diff,overtime=self.calculate_delay_diff_overtime(psave['shift_rec'],new_att.check_in,psave['time'],shift_record)
                            new_att.write({ 'check_out': psave['time'],
                                                'is_process':True,
                                                
                                                'act_delay_time':delay,
                                            'act_diff_time':diff,
                                            'act_over_time':overtime,
                                                
                                            })
                    else:
                        # if it is just read one record of biometric
                        for punch_rec in rec_shift:
                            shift_obj=self.env['shift_data'].browse(punch_rec['shift'])
                            new_att=self.env['hr.attendance'].create({'employee_id': emp[0],
                                            'check_in': punch_rec['time'],
                                            'att_shift_rec':punch_rec['shift_rec'].id,
                                            'match_shift':punch_rec['shift'],
                                            'expected_check_in':shift_obj.hour_from,
                                            'expected_check_out':shift_obj.hour_to,
                                            })

