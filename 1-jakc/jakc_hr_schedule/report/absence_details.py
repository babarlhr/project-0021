from datetime import datetime
import pytz
import time
from openerp import tools
from openerp.osv import osv
from openerp.report import report_sxw

class absence_details(report_sxw.rml_parse):

    def _get_employees(self, ids):
        employee_obj = self.pool.get('hr.employee')
        return employee_obj.search(self.cr, self.uid, ids)

    def _get_employee_name(self, employee_id):
        employee_obj = self.pool.get('hr.employee')
        return employee_obj.browse(self.cr, self.uid, employee_id)['name']

    def _get_schedule_detail(self, employee_id, start_date, end_date):
        args = [('employee_id', '=', employee_id), '&', ('day', '>=', start_date),('day', '<=', end_date)]
        schedule_detail_obj = self.pool.get('hr.schedule.detail')
        schedule_detail_ids = schedule_detail_obj.search(self.cr, self.uid, args, order='day asc')
        schedule_details = schedule_detail_obj.browse(self.cr, self.uid, schedule_detail_ids)
        return schedule_details

    def _get_schedule_detail_count(self, employee_id, start_date, end_date):
        args = [('employee_id', '=', employee_id), '&', ('day', '>=', start_date), ('day', '<=', end_date), ]
        schedule_detail_obj = self.pool.get('hr.schedule.detail')
        schedule_detail_ids = schedule_detail_obj.search(self.cr, self.uid, args, order='day asc')
        return len(schedule_detail_ids)

    def _get_schedule_detail_not_work_count(self, employee_id, start_date, end_date):
        args = [('employee_id', '=', employee_id), '&', ('day', '>=', start_date), ('day', '<=', end_date),
                ('type', 'in', ['off','holiday']),]
        schedule_detail_obj = self.pool.get('hr.schedule.detail')
        schedule_detail_ids = schedule_detail_obj.search(self.cr, self.uid, args, order='day asc')
        return len(schedule_detail_ids)

    def _get_schedule_detail_work_count(self, employee_id, start_date, end_date):
        args = [('employee_id', '=', employee_id), '&', ('day', '>=', start_date), ('day', '<=', end_date),
                ('type', '=', 'work'),('state','=','locked')]
        schedule_detail_obj = self.pool.get('hr.schedule.detail')
        schedule_detail_ids = schedule_detail_obj.search(self.cr, self.uid, args, order='day asc')
        return len(schedule_detail_ids)

    def _get_schedule_detail_exception_count(self, employee_id, start_date, end_date):
        args = [('employee_id', '=', employee_id), '&', ('day', '>=', start_date), ('day', '<=', end_date),
                ('type', '=', 'work'), ('state', '=', 'exception')]
        schedule_detail_obj = self.pool.get('hr.schedule.detail')
        schedule_detail_ids = schedule_detail_obj.search(self.cr, self.uid, args, order='day asc')
        return len(schedule_detail_ids)

    def _get_schedule_detail_holiday_count(self, employee_id, start_date, end_date):
        args = [('employee_id', '=', employee_id), '&', ('day', '>=', start_date), ('day', '<=', end_date),
                ('type', '=', 'holiday')]
        schedule_detail_obj = self.pool.get('hr.schedule.detail')
        schedule_detail_ids = schedule_detail_obj.search(self.cr, self.uid, args, order='day asc')
        return len(schedule_detail_ids)


    def __init__(self, cr, uid, name, context):
        super(absence_details, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'datetime': datetime,
            'get_employees': self._get_employees,
            'get_employee_name': self._get_employee_name,
            'get_schedule_detail': self._get_schedule_detail,
            'get_schedule_detail_count': self._get_schedule_detail_count,
            'get_schedule_detail_not_work_count': self._get_schedule_detail_not_work_count,
            'get_schedule_detail_work_count': self._get_schedule_detail_work_count,
            'get_schedule_detail_work_exception': self._get_schedule_detail_exception_count,
            'get_schedule_detail_holiday_count': self._get_schedule_detail_holiday_count,
        })


class report_absence_details(osv.AbstractModel):
    _name = 'report.jakc_hr_schedule.report_absencedetails'
    _inherit = 'report.abstract_report'
    _template = 'jakc_hr_schedule.report_absencedetails'
    _wrapped_report_class = absence_details


