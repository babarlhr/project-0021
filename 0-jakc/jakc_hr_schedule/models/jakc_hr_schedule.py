import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from pytz import timezone, utc
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as OE_DTFORMAT
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as OE_DFORMAT
from openerp.tools.translate import _
import math

from openerp import netsvc
from openerp import fields, models, api, _
from openerp.exceptions import Warning, ValidationError
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


AVAILABLE_SCHEDULE_STATES = [
    ('draft', 'Draft'),
    ('validate', 'Confirmed'),
    ('locked', 'Locked'),
    ('unlocked', 'Unlocked'),
]

AVAILABLE_SCHEDULE_DETAIL_STATES = [
    ('draft', 'Draft'),
    ('validate', 'Confirmed'),
    ('exception', 'Exception'),
    ('locked', 'Locked'),
    ('unlocked', 'Unlocked'),
]

AVAILABLE_TYPE_STATES = [
    ('missedp', 'Missed Punch'),
    ('adjp', 'Punch Adjustment'),
    ('absence', 'Absence'),
    ('schedadj', 'Schedule Adjustment'),
    ('other', 'Other'),
]

AVAILABLE_SEVERITY_STATES = [
    ('low', 'Low'),
    ('medium', 'Medium'),
    ('high', 'High'),
    ('critical', 'Critical'),
]

AVAILABLE_ALERT_STATES =[
    ('unresolved', 'Unresolved'),
    ('resolved', 'Resolved'),
]

DAYOFWEEK_SELECTION = [
    ('0', 'Monday'),
    ('1', 'Tuesday'),
    ('2', 'Wednesday'),
    ('3', 'Thursday'),
    ('4', 'Friday'),
    ('5', 'Saturday'),
    ('6', 'Sunday'),
]


class HrScheduleHoliday(models.Model):
    _name = 'hr.schedule.holiday'

    name = fields.Date('Date', required=True)
    description = fields.Char('Description', size=200, required=True)


class HrScheduleShift(models.Model):
    _name = 'hr.schedule.shift'

    @api.multi
    def float_time_convert(self, float_val):
        factor = float_val < 0 and -1 or 1
        val = abs(float_val)
        return str(factor * int(math.floor(val))).zfill(2), str(int(round((val % 1) * 60))).zfill(2)

    name = fields.Char('Name', required=False, readonly=True)
    code = fields.Char('Code', required=True)
    iface_active = fields.Boolean('Active', default=False)
    start_hours = fields.Float('Start Hours', required=True)
    end_hours = fields.Float('End Hours', required=True)
    iface_next_day = fields.Boolean('Next Day', default=False)

    @api.model
    def create(self, vals):
        hours, minutes = self.float_time_convert(vals.get('start_hours'))
        str_start_hours = hours + ":" + minutes
        hours, minutes = self.float_time_convert(vals.get('end_hours'))
        str_end_hours = hours + ":" + minutes
        vals['name'] = vals.get('code') + " (" + str_start_hours + " - " + str_end_hours + ")"
        res = super(HrScheduleShift, self).create(vals)
        return res


class HrSchedule(models.Model):
    _name = 'hr.schedule'
    _inherit = ['mail.thread']
    _description = 'HR Schedule Management'

    @api.multi
    def _check_date(self, employee_id, date_start, date_end):
        schedule_detail_obj = self.env['hr.schedule.detail']
        args = [('employee_id', '=', employee_id),('day', '>=', date_start), ('day', '<=', date_end)]
        schedule_detail_ids = schedule_detail_obj.search(args)
        print schedule_detail_ids
        if len(schedule_detail_ids) > 0:
            return False
        return True

    @api.multi
    def float_time_convert(self, float_val):
        factor = float_val < 0 and -1 or 1
        val = abs(float_val)
        return str(factor * int(math.floor(val))).zfill(2), str(int(round((val % 1) * 60))).zfill(2)

    @api.onchange('employee_id', 'date_start', 'date_end')
    def onchange_employee_start_date(self):

        dStart = False
        edata = False

        if self.employee_id:
            edata = self.env['hr.employee'].browse(self.employee_id.id)

        if self.date_start:
            dStart = datetime.strptime(self.date_start, '%Y-%m-%d').date()
            # The schedule must start on a Monday
            #if dStart.weekday() != 0:
                #self.date_start = False
            #    self.date_end = False
            #else:
            #    dEnd = dStart + relativedelta(days=+6)
            #    self.date_end = dEnd.strftime('%Y-%m-%d')

        if edata:
            self.name = edata['name']
            if dStart:
                self.name = self.name + ': ' + \
                            dStart.strftime('%Y-%m-%d') + ' Wk ' + \
                            str(dStart.isocalendar()[1])

            if 'contract_id' in edata:
                cdata = self.env['hr.contract'].browse(edata['contract_id'].id)
                if cdata['working_hours']:
                    self.template_id = cdata['working_hours']
                else:
                    self.template_id = ''
            else:
                self.template_id = ''

    def _is_holiday(self, day):
        schedule_holiday_obj = self.env['hr.schedule.holiday']
        args=[('name','=', day)]
        schedule_holiday_ids = schedule_holiday_obj.search(args)
        if len(schedule_holiday_ids) > 0:
            return True
        else:
            return False

    @api.multi
    def create_details(self, sched_id):
        schedule = self.browse(sched_id)
        if schedule.template_id:
            user = self.env['res.users'].browse(self.env.uid)
            local_tz = timezone(user.tz)
            dCount = datetime.strptime(schedule.date_start, '%Y-%m-%d').date()
            dCountEnd = datetime.strptime(schedule.date_end, '%Y-%m-%d').date()
            dWeekStart = dCount
            dSchedStart = dCount
            while dCount <= dCountEnd:
                prevutcdtStart = False
                prevDayofWeek = False
                weekday = str(dCount.weekday())
                template_id = schedule.template_id.id
                args = [('calendar_id','=', template_id),('')]

                while dCount <= dCountEnd:
                    val = {
                        'name': schedule.name,
                        'type': 'work',
                        'dayofweek': str(dCount.weekday()),
                        'day': dCount,
                        'schedule_id': sched_id,
                    }
                    self.env['hr.schedule.detail'].create(val)
                    dCount += relativedelta(days=+1)

                for worktime in schedule.template_id.attendance_ids:

                    hour, minute = self.float_time_convert(worktime.hour_from)
                    toHour, toMin = self.float_time_convert(worktime.hour_to)

                    # TODO - Someone affected by DST should fix this
                    #
                    dtStart = datetime.strptime(dWeekStart.strftime(
                        '%Y-%m-%d') + ' ' + hour + ':' + minute + ':00',
                                                '%Y-%m-%d %H:%M:%S')
                    locldtStart = local_tz.localize(dtStart, is_dst=False)
                    utcdtStart = locldtStart.astimezone(utc)
                    if worktime.dayofweek != 0:
                        utcdtStart = utcdtStart + \
                                     relativedelta(days=+int(worktime.dayofweek))
                    dDay = utcdtStart.astimezone(local_tz).date()

                    # If this worktime is a continuation (i.e - after lunch)
                    # set the start time based on the difference from the
                    # previous record
                    #
                    if prevDayofWeek and prevDayofWeek == worktime.dayofweek:
                        prevHour = prevutcdtStart.strftime('%H')
                        prevMin = prevutcdtStart.strftime('%M')
                        curHour = utcdtStart.strftime('%H')
                        curMin = utcdtStart.strftime('%M')
                        delta_seconds = (
                            datetime.strptime(curHour + ':' + curMin, '%H:%M')
                            - datetime.strptime(prevHour + ':' + prevMin,
                                                '%H:%M')).seconds
                        utcdtStart = prevutcdtStart + \
                                     timedelta(seconds=+delta_seconds)
                        dDay = prevutcdtStart.astimezone(local_tz).date()

                    delta_seconds = (datetime.strptime(toHour + ':' + toMin,
                                                       '%H:%M')
                                     - datetime.strptime(hour + ':' + minute,
                                                         '%H:%M')).seconds
                    utcdtEnd = utcdtStart + timedelta(seconds=+delta_seconds)

                    if True:
                        val = {
                            'name': schedule.name,
                            'type': worktime.type,
                            'dayofweek': worktime.dayofweek,
                            'day': dDay,
                            'date_start': utcdtStart.strftime(
                                '%Y-%m-%d %H:%M:%S'),
                            'date_end': utcdtEnd.strftime(
                                '%Y-%m-%d %H:%M:%S'),
                            'schedule_id': sched_id,
                        }
                        self.env['hr.schedule.detail'].create(val)

                    prevDayofWeek = worktime.dayofweek
                    prevutcdtStart = utcdtStart

                dCount = dWeekStart + relativedelta(weeks=+1)
                dWeekStart = dCount
        else:
            user = self.env['res.users'].browse(self.env.uid)
            local_tz = timezone(user.tz)
            dCount = datetime.strptime(schedule.date_start, '%Y-%m-%d').date()
            dCountEnd = datetime.strptime(schedule.date_end, '%Y-%m-%d').date()
            while dCount <= dCountEnd:
                if self._is_holiday(dCount):
                    type = 'holiday'
                else:
                    type = 'work'
                val = {
                    'name': schedule.name,
                    'type': type,
                    'dayofweek':  str(dCount.weekday()),
                    'day': dCount,
                    'schedule_id': sched_id,
                }
                self.env['hr.schedule.detail'].create(val)
                dCount += relativedelta(days=+1)

        return True

    @api.multi
    def trans_validate(self):
        for detail in self.detail_ids:
            if not detail.shift_id and not detail.type in ['holiday','off']:
                raise ValidationError('Please Complete All Schedule')
            detail.write({'state': 'validate'})
        self.write({'state':'validate'})

    name = fields.Char('Name',size=50, required=True, readonly=True, states={'draft': [('readonly', False)]})
    company_id = fields.Many2one('res.company','Company', readonly=True)
    employee_id = fields.Many2one('hr.employee','Employee', required=True, readonly=True, states={'draft': [('readonly', False)]})
    template_id = fields.Many2one('resource.calendar', 'Schedule Template', readonly=True, states={'draft': [('readonly', False)]})
    detail_ids = fields.One2many('hr.schedule.detail','schedule_id','Schedule Detail', readonly=True, states={'draft': [('readonly', False)]})
    date_start = fields.Date('Start Date', required=True)
    date_end = fields.Date('End Date', required=True)
    department_id = fields.Many2one('hr.department', 'Department', related='employee_id.department_id', store=True)
    state = fields.Selection(AVAILABLE_SCHEDULE_STATES, 'Status', required=True, readonly=True, default='draft')

    @api.model
    def create(self, vals):

        if datetime.strptime(vals.get('date_start') + ' 00:00:00','%Y-%m-%d %H:%M:%S').date() > datetime.strptime(vals.get('date_end') + ' 00:00:00','%Y-%m-%d %H:%M:%S').date():
            raise ValidationError('End Date must bigger than Start Date!')

        if not self._check_date(vals.get('employee_id'), vals.get('date_start'), vals.get('date_end')):
            raise ValidationError('Cannot overlap employee schedule!')

        res = super(HrSchedule, self).create(vals)
        self.create_details(res.id)
        return res

    @api.constrains('date_start')
    def _schedule_date(self):
            for shd in self:
                self.env.cr.execute("""\
                    SELECT id
                    FROM hr_schedule
                    WHERE (date_start <= %s and %s <= date_end)
                      AND employee_id=%s
                      AND id <> %s""", (shd.date_end, shd.date_start, shd.employee_id.id, shd.id))
                if self.env.cr.fetchall():
                    return ValidationError('You cannot have schedules that overlap!')
            return True


    @api.model
    def create_mass_schedule(self):
        """Creates tentative schedules for all employees based on the
        schedule template attached to their contract. Called from the
        scheduler.
        """

        sched_obj = self.env['hr.schedule']
        ee_obj = self.env['hr.employee']
        dept_obj = self.env['hr.department']

        # Create a two-week schedule beginning from Monday of next week.
        #
        dt = datetime.today()
        days = 7 - dt.weekday()
        dt += relativedelta(days=+days)
        dStart = dt.date()
        dEnd = dStart + relativedelta(weeks=+2, days=-1)

        # Create schedules for each employee in each department
        #
        dept_ids = dept_obj.search([])
        for dept in dept_obj.browse(dept_ids):
            ee_ids = ee_obj.search([('department_id', '=', dept.id)], order="name")
            if len(ee_ids) == 0:
                continue

            for ee in ee_obj.browse(ee_ids):
                if not ee.contract_id or not ee.contract_id.schedule_template_id:
                    continue

                sched = {
                    'name': (ee.name + ': ' + dStart.strftime('%Y-%m-%d') +
                             ' Wk ' + str(dStart.isocalendar()[1])),
                    'employee_id': ee.id,
                    'template_id': ee.contract_id.schedule_template_id.id,
                    'date_start': dStart.strftime('%Y-%m-%d'),
                    'date_end': dEnd.strftime('%Y-%m-%d'),
                }
                sched_obj.create(sched)


class HrScheduleDetail(models.Model):
    _name = 'hr.schedule.detail'
    _inherit = 'mail.thread'
    _description = 'HR Schedule Detail'
    _order = 'day asc'

    @api.multi
    def float_time_convert(self, float_val):
        factor = float_val < 0 and -1 or 1
        val = abs(float_val)
        return str(factor * int(math.floor(val))).zfill(2), str(int(round((val % 1) * 60))).zfill(2)

    @api.one
    def _worked_hours_compute(self):
        """For each hr.attendance record of action sign-in: assign 0.
        For each hr.attendance record of action sign-out: assign number of hours since last sign-in.
        """
        if self.actual_in and self.actual_out:
            start_date = datetime.strptime(self.actual_in,'%Y-%m-%d %H:%M:%S')
            end_date = datetime.strptime(self.actual_out,'%Y-%m-%d %H:%M:%S')
            sch_start_date = datetime.strptime(self.date_start, '%Y-%m-%d %H:%M:%S')
            sch_end_date = datetime.strptime(self.date_end, '%Y-%m-%d %H:%M:%S')

            self.working_hours = (end_date - start_date).seconds

            self.schedule_hours = (sch_end_date - sch_start_date).seconds

            if start_date < sch_start_date:
                diff_start_date = sch_start_date
            else:
                diff_start_date = start_date

            if end_date > sch_end_date:
                diff_end_date = sch_end_date
            else:
                diff_end_date = end_date

            #diff_hours_employee = diff_end_date - diff_start_date

            self.diff_hours = self.working_hours - self.schedule_hours

            #self.diff_hours = diff_hours_employee - self.schedule_hours

            if sch_start_date < start_date:
                self.hours_before_in = -1 * (start_date -  sch_start_date).seconds
            else:
                self.hours_before_in = (sch_start_date - start_date).seconds

            if sch_end_date > end_date:
                self.hours_after_out = -1 * (sch_end_date - end_date).seconds
            else:
                self.hours_after_out = (end_date - sch_end_date).seconds

            print "Compute Successfully"
        else:
            self.working_hours = 0

    @api.one
    def _calculate_working(self):
        hours = self.working_hours / 60 / 60
        minutes = (self.working_hours / 60) - (hours * 60)
        self.working_hours_str = str(hours).zfill(2) + ':' + str(minutes).zfill(2)

    @api.one
    def _calculate_schedule(self):
        hours = self.schedule_hours / 60 / 60
        minutes = (self.schedule_hours / 60) - (hours * 60)
        self.schedule_hours_str = str(hours).zfill(2) + ':' + str(minutes).zfill(2)

    @api.one
    def _calculate_diff(self):
        if self.diff_hours < 0:
            diff_hours = -1 * self.diff_hours
        else:
            diff_hours = self.diff_hours

        hours = diff_hours / 60 / 60
        minutes = (diff_hours / 60) - (hours * 60)

        if self.diff_hours < 0:
            self.diff_hours_str = '-' + str(hours).zfill(2) + ':' + str(minutes).zfill(2)
        else:
            self.diff_hours_str = str(hours).zfill(2) + ':' + str(minutes).zfill(2)

    @api.one
    def _calculate_diff_late_in(self):
        start_date = datetime.strptime(self.actual_in, '%Y-%m-%d %H:%M:%S')
        end_date = datetime.strptime(self.actual_out, '%Y-%m-%d %H:%M:%S')
        sch_start_date = datetime.strptime(self.date_start, '%Y-%m-%d %H:%M:%S')
        sch_end_date = datetime.strptime(self.date_end, '%Y-%m-%d %H:%M:%S')
        if start_date < sch_start_date:
            self.diff_late_in = 0
        else:
            self.diff_late_in = (start_date - sch_start_date).seconds

    @api.one
    def _calculate_diff_early_out(self):
        start_date = datetime.strptime(self.actual_in, '%Y-%m-%d %H:%M:%S')
        end_date = datetime.strptime(self.actual_out, '%Y-%m-%d %H:%M:%S')
        sch_start_date = datetime.strptime(self.date_start, '%Y-%m-%d %H:%M:%S')
        sch_end_date = datetime.strptime(self.date_end, '%Y-%m-%d %H:%M:%S')
        if end_date > sch_end_date:
            self.diff_early_out = 0
        else:
            self.diff_early_out = (sch_end_date - end_date).seconds

    def _calculate_hours_before_in(self):
        if self.hours_before_in < 0:
            hours_before_in = -1 * self.hours_before_in
        else:
            hours_before_in = self.hours_before_in

        hours = hours_before_in / 60 / 60
        minutes = (hours_before_in / 60) - (hours * 60)

        if self.hours_before_in < 0:
            self.hours_before_in_str = '-' + str(hours).zfill(2) + ':' + str(minutes).zfill(2)
        else:
            self.hours_before_in_str = str(hours).zfill(2) + ':' + str(minutes).zfill(2)

    @api.one
    def _calculate_hours_after_out(self):
        if self.hours_after_out < 0:
            hours_after_out = -1 * self.hours_after_out
        else:
            hours_after_out = self.hours_after_out

        hours = hours_after_out / 60 / 60
        minutes = (hours_after_out / 60) - (hours * 60)

        if self.hours_after_out < 0:
            self.hours_after_out_str = '-' + str(hours).zfill(2) + ':' + str(minutes).zfill(2)
        else:
            self.hours_after_out_str = str(hours).zfill(2) + ':' + str(minutes).zfill(2)

    @api.multi
    def trans_exception(self):
        print "Transaction Exception"
        ir_model_data_obj = self.env['ir.model.data']
        res = ir_model_data_obj.get_object_reference('jakc_hr_schedule', 'wizard_process_exception_form_view')
        return {
            'name': 'Confirm Exception',
            'view_type': 'form',
            "view_mode": 'form',
            'res_model': [res and res[1] or False],
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
        }

    @api.one
    def locked(self):
        status = False
        count = 0
        exception_count = len(self.exception_ids)
        for exception in self.exception_ids:
            if exception.state == 'approve':
                count += 1

        if exception_count == count:
            self.state = 'locked'

    name = fields.Char('Name', size=64, required=True)
    dayofweek = fields.Selection(DAYOFWEEK_SELECTION, 'Day of Week', required=True, default=0)
    shift_id = fields.Many2one('hr.schedule.shift', 'Shift', required=False)
    date_start = fields.Datetime('Start Date', required=False)
    date_end = fields.Datetime('End Date', required=False)
    day = fields.Date('Day', required=True)
    schedule_id = fields.Many2one('hr.schedule','Schedule', required=True)
    type = fields.Selection([('work','Work'),('off','Off'),('holiday','Holiday')],'Type', required=True, default='work')
    employee_id = fields.Many2one('hr.employee', 'Employee', related='schedule_id.employee_id', store=True)
    department_id = fields.Many2one('hr.department','Department', related='schedule_id.department_id', store=True)
    state = fields.Selection(AVAILABLE_SCHEDULE_DETAIL_STATES, 'Status', required=True, readonly=True, default='draft')

    actual_in = fields.Datetime('Actual In')
    actual_out = fields.Datetime('Actual Out')

    working_hours = fields.Integer('Hours', default=0)
    working_hours_str = fields.Char('Working', compute="_calculate_working")

    schedule_hours = fields.Integer('Schedule Hours', default=0)
    schedule_hours_str = fields.Char('Schedule', compute="_calculate_schedule")

    diff_hours = fields.Integer('Different')
    diff_hours_str = fields.Char('Diffrents', compute="_calculate_diff")

    diff_late_in = fields.Integer(compute='_calculate_diff_late_in', string='Diff Late In')
    diff_early_out = fields.Integer(compute='_calculate_dif_early_out', string='Diff Early Out')

    hours_before_in = fields.Integer('Hours Before In', default=0)
    hours_before_in_str = fields.Char('Before In', compute="_calculate_hours_before_in")

    hours_after_out = fields.Integer('Hours After Out', default=0)
    hours_after_out_str = fields.Char('After Out', compute="_calculate_hours_after_out")

    absence_ids = fields.One2many('hr.absence','schedule_detail_id', 'Absences')
    exception_ids = fields.One2many('hr.schedule.detail.exception', 'schedule_detail_id','Exceptions')

    @api.multi
    def validate_schedule_detail(self):
        i = 0
        exception_number = len(self.exception_ids)
        for line in self.exception_ids:
            if line.state == 'approve':
                i += 1
        if i == exception_number:
            self.sudo().write({'state':'locked'})


    @api.multi
    def process_absence(self):
        schedule_detail_exception_obj = self.env['hr.schedule.detail.exception']
        if len(self.absence_ids) == 0:
            values = {}
            values.update({'schedule_detail_id': self.id})
            values.update({'exception_code': 'noswapin'})
            schedule_detail_exception_obj.create(values)
            values = {}
            values.update({'schedule_detail_id': self.id})
            values.update({'exception_code': 'noswapout'})
            schedule_detail_exception_obj.create(values)
            self.write({'state': 'exception'})
        if len(self.absence_ids) == 1:
            absence = self.absence_ids[0]
            if absence.trans_date_time < self.date_start:
                values = {}
                values.update({'schedule_detail_id': self.id})
                values.update({'exception_code': 'noswapout'})
                schedule_detail_exception_obj.create(values)
                actual_out = datetime.strptime(self.date_end, '%Y-%m-%d %H:%M:%S') + timedelta(hours=-3)
                self.write({'actual_in': absence.trans_date_time, 'actual_out': actual_out.strftime('%Y-%m-%d %H:%M:%S'), 'state':'locked'})
                self._worked_hours_compute()
            elif absence.trans_date_time > self.date_end:
                values = {}
                values.update({'schedule_detail_id': self.id})
                values.update({'exception_code': 'noswapin'})
                schedule_detail_exception_obj.create(values)
                actual_in = datetime.strptime(self.date_start, '%Y-%m-%d %H:%M:%S') + timedelta(hours=4.5)
                self.write({'actual_in': actual_in.strftime('%Y-%m-%d %H:%M:%S'), 'actual_out': absence.trans_date_time, 'state': 'locked'})
                self._worked_hours_compute()
            elif absence.trans_date_time < (datetime.strptime(self.date_start, '%Y-%m-%d %H:%M:%S') + timedelta(hours=4)).strftime('%Y-%m-%d %H:%M:%S'):
                values = {}
                values.update({'schedule_detail_id': self.id})
                values.update({'exception_code': 'latein'})
                schedule_detail_exception_obj.create(values)
                values = {}
                values.update({'schedule_detail_id': self.id})
                values.update({'exception_code': 'noswapout'})
                schedule_detail_exception_obj.create(values)
                actual_out = datetime.strptime(self.date_end, '%Y-%m-%d %H:%M:%S') + timedelta(hours=-3)
                self.write({'actual_in': absence.trans_date_time, 'actual_out': datetime.strptime(self.date_end, '%Y-%m-%d %H:%M:%S') + timedelta(hours=-3), 'state': 'locked'})
                self._worked_hours_compute()
            elif absence.trans_date_time > (datetime.strptime(self.date_end, '%Y-%m-%d %H:%M:%S') + timedelta(hours=-4)).strftime('%Y-%m-%d %H:%M:%S'):
                values = {}
                values.update({'schedule_detail_id': self.id})
                values.update({'exception_code': 'earlyout'})
                schedule_detail_exception_obj.create(values)
                values = {}
                values.update({'schedule_detail_id': self.id})
                values.update({'exception_code': 'noswapin'})
                schedule_detail_exception_obj.create(values)
                actual_in = datetime.strptime(self.date_start, '%Y-%m-%d %H:%M:%S') + timedelta(hours=4.5)
                self.write({'actual_in': actual_in.strftime('%Y-%m-%d %H:%M:%S'),'actual_out': absence.trans_date_time, 'state': 'locked'})
                self._worked_hours_compute()

        if len(self.absence_ids) > 1:
            iface_swapin = False
            iface_swapout = False
            iface_latein = False
            iface_earlyout = False
            actual_in = None
            actual_out = None

            for absence in self.absence_ids:
                if absence.trans_date_time < self.date_start:
                    if not actual_in:
                        actual_in = absence.trans_date_time
                        iface_swapin = True
                    else:
                        if actual_in < absence.trans_date_time:
                            continue
                        else:
                            actual_in = absence.trans_date_time
                    continue

                if absence.trans_date_time > self.date_end:
                    if not actual_out:
                        actual_out = absence.trans_date_time
                        iface_swapout = True
                    else:
                        if actual_out > absence.trans_date_time:
                            continue
                        else:
                            actual_out = absence.trans_date_time
                    continue

                start_date = datetime.strptime(self.date_start, '%Y-%m-%d %H:%M:%S') + timedelta(hours=4)

                if absence.trans_date_time < start_date.strftime('%Y-%m-%d %H:%M:%S'):
                    if not actual_in:
                        actual_in = absence.trans_date_time
                        iface_latein = True
                    else:
                        if actual_in < absence.trans_date_time:
                            continue
                        else:
                            actual_in = absence.trans_date_time
                    continue

                end_date = datetime.strptime(self.date_end, '%Y-%m-%d %H:%M:%S') + timedelta(hours=-4)

                if absence.trans_date_time > end_date.strftime('%Y-%m-%d %H:%M:%S'):
                    if not actual_out:
                        actual_out = absence.trans_date_time
                        iface_earlyout = True
                    else:
                        if actual_out < absence.trans_date_time:
                            continue
                        else:
                            actual_out = absence.trans_date_time
                    continue

            if iface_swapin and iface_swapout:
                values = {}
                values.update({'actual_in': actual_in})
                values.update({'actual_out': actual_out})
                values.update({'state': 'locked'})
                self.write(values)
                self._worked_hours_compute()

            if iface_swapin and not iface_swapout:
                if not iface_earlyout:
                    values = {}
                    values.update({'schedule_detail_id': self.id})
                    values.update({'exception_code': 'noswapout'})
                    schedule_detail_exception_obj.create(values)
                    actual_out = datetime.strptime(self.date_end, '%Y-%m-%d %H:%M:%S') + timedelta(hours=-3)
                    self.write({'actual_in': actual_in, 'actual_out': actual_out.strftime('%Y-%m-%d %H:%M:%S'), 'state': 'locked'})
                    self._worked_hours_compute()
                else:
                    values = {}
                    values.update({'schedule_detail_id': self.id})
                    values.update({'exception_code': 'earlyout'})
                    schedule_detail_exception_obj.create(values)
                    self.write({'actual_in': actual_in, 'actual_out': actual_out, 'state': 'locked'})
                    self._worked_hours_compute()

            if not iface_swapin and iface_swapout:
                if not iface_latein:
                    values = {}
                    values.update({'schedule_detail_id': self.id})
                    values.update({'exception_code': 'noswapin'})
                    schedule_detail_exception_obj.create(values)
                    actual_in = datetime.strptime(self.date_start, '%Y-%m-%d %H:%M:%S') + timedelta(hours=4.5)
                    self.write({'actual_in': actual_in.strftime('%Y-%m-%d %H:%M:%S'), 'actual_out': actual_out, 'state': 'locked'})
                    self._worked_hours_compute()
                else:
                    values = {}
                    values.update({'schedule_detail_id': self.id})
                    values.update({'exception_code': 'latein'})
                    schedule_detail_exception_obj.create(values)
                    self.write({'actual_in': actual_in, 'actual_out': actual_out, 'state': 'locked'})
                    self._worked_hours_compute()

            if iface_latein and iface_earlyout:
                values = {}
                values.update({'schedule_detail_id': self.id})
                values.update({'exception_code': 'latein'})
                schedule_detail_exception_obj.create(values)
                values = {}
                values.update({'schedule_detail_id': self.id})
                values.update({'exception_code': 'earlyout'})
                schedule_detail_exception_obj.create(values)
                self.write({'actual_in': actual_in, 'actual_out': actual_out, 'state': 'locked'})
                self._worked_hours_compute()


    _order = 'schedule_id, date_start, dayofweek'

    @api.model
    def create(self, vals):
        if 'day' not in vals and 'date_start' in vals:
            # TODO - Someone affected by DST should fix this
            #
            user = self.env['res.users'].browse(self.env.uid)
            local_tz = timezone(user.tz)
            dtStart = datetime.strptime(vals['date_start'], OE_DTFORMAT)
            locldtStart = local_tz.localize(dtStart, is_dst=False)
            utcdtStart = locldtStart.astimezone(utc)
            dDay = utcdtStart.astimezone(local_tz).date()
            vals.update({'day': dDay})

        res = super(HrScheduleDetail, self).create(vals)
        return res

    @api.multi
    def write(self, vals):
        res = super(HrScheduleDetail, self).write(vals)
        if 'shift_id' in vals:
            user = self.env['res.users'].browse(self.env.uid)
            local_tz = timezone(user.tz)
            shift_id = self.shift_id
            shift_day = self.day

            hours, minutes = self.float_time_convert(shift_id.start_hours)
            date_start = datetime.strptime(shift_day + " " + hours + ":" + minutes + ":00",'%Y-%m-%d %H:%M:%S')
            locldtStart = local_tz.localize(date_start, is_dst=False)
            self.date_start = locldtStart.astimezone(utc)

            hours, minutes = self.float_time_convert(shift_id.end_hours)
            if shift_id.iface_next_day:
                shift_day = (datetime.strptime(shift_day, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
            date_end = datetime.strptime(shift_day + " " + hours + ":" + minutes + ":00", '%Y-%m-%d %H:%M:%S')
            locldtEnd = local_tz.localize(date_end, is_dst=False)
            self.date_end = locldtEnd.astimezone(utc)
        return res

    @api.multi
    def _rec_message(self):
        return _('You cannot have scheduled days that overlap!')


class HrScheduleDetailException(models.Model):
    _name = 'hr.schedule.detail.exception'

    schedule_detail_id = fields.Many2one('hr.schedule.detail','Schedule Detail #', readonly=True)
    employee_id = fields.Many2one('hr.employee','Employee', related='schedule_detail_id.employee_id', readonly=True)
    day = fields.Date(string='Date', store=True, related='schedule_detail_id.day',readonly=True)
    exception_code = fields.Selection([('normal', 'Normal'),
                                       ('normexcept', 'Normal with Exception'),
                                       ('noswapin', 'No Swap-In'),
                                       ('noswapout', 'No Swap-Out'),
                                       ('latein', 'Late In'),
                                       ('earlyout', 'Early Out'), ], 'Exception')
    exception_request_date = fields.Datetime('Exception Request Date', readonly=True)
    #exception_reason = fields.Selection([
    #                                        ('01','Dinas Luar Non Fullday/Non Fullboard'),
    #                                        ('02','Dinas Luar Fullday/Fullboard'),
    #                                        ('03','Cuti'),
    #                                        ('04', 'Ijin'),
    #                                        ('05', 'Ijin Sakit'),
    #                                        ('06','Tugas Belajar'),
    #                                        ('99', 'Lain - Lain')
    #                                    ], 'Exception Reason', readonly=True)
    exception_reason = fields.Many2one('hr.exception.reason','Exception Reason', readonly=True)
    exception_description = fields.Text('Exception Description', readonly=True)
    approved_datetime = fields.Datetime('Approved/Rejected Date', readonly=True)
    approved_state = fields.Selection([
                                        ('approve', 'Approve'),
                                        ('reject', 'Reject'),
                                        ], readonly=True)
    approved_by = fields.Many2one('hr.employee', 'Approved By', readonly=True)
    approved_reason = fields.Text('Rejected Reason', reaodnly=True)
    state = fields.Selection([('open', 'Open'),
                             ('request', 'Request for Approval'),
                              ('approve', 'Approve'),
                              ('reject','Reject'),], default='open', readonly=True)

class HrExceptionReason(models.Model):
    _name = 'hr.exception.reason'

    name = fields.Char('Code', size=10, required=True)
    description = fields.Char('Description', size=100, required=True)
    iface_presence = fields.Boolean('Presence', default=False)
    iface_description = fields.Boolean('Description Needed', default=False)

class HrChangeRequest(models.Model):
    _name = 'hr.change.request'

    change_date = fields.Date()
    schedule_detail_id = fields.Many2one('hr.schedule.detail', 'Schedule Detail #')
    schedule_date_start = fields.Datetime(comodel_name='hr.schedule.detail', string='Schedule Start Date', store=True,
                                          related='schedule_detail_id.date_start', readonly=True)
    schedule_date_end = fields.Datetime(comodel_name='hr.schedule.detail', string='Schedule End Date', store=True,
                                          related='schedule_detail_id.date_end', readonly=True)

    date_start = fields.Date('Start Date', required=True)
    date_end = fields.Datetime('End Date', required=True)
