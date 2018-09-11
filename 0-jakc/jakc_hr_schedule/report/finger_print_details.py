from datetime import datetime
import pytz
import time
from openerp import tools
from openerp.osv import osv
from openerp.report import report_sxw

class fingerprint_details(report_sxw.rml_parse):

    def _get_employees(self, ids):
        employee_obj = self.pool.get('hr.employee')
        return employee_obj.search(self.cr, self.uid, ids)

    def _get_employee_name(self, employee_id):
        employee_obj = self.pool.get('hr.employee')
        return employee_obj.browse(self.cr, self.uid, employee_id)['name']

    def _get_fingerprint_detail(self, employee_id, start_date, end_date):
        start_date += ' 00:00:00'
        end_date += ' 23:59:00'
        args = [('name', '=', employee_id), '&', ('trans_date_time', '>=', start_date),('trans_date_time', '<=', end_date)]
        absence_obj = self.pool.get('hr.absence')
        absence_ids = absence_obj.search(self.cr, self.uid, args, order='trans_date_time asc')
        absences = absence_obj.browse(self.cr, self.uid, absence_ids)
        return absences

    def __init__(self, cr, uid, name, context):
        super(fingerprint_details, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'get_employees': self._get_employees,
            'get_employee_name': self._get_employee_name,
            'get_fingerprint_detail': self._get_fingerprint_detail,
        })


class report_absence_details(osv.AbstractModel):
    _name = 'report.jakc_hr_schedule.report_fingerprintdetails'
    _inherit = 'report.abstract_report'
    _template = 'jakc_hr_schedule.report_fingerprintdetails'
    _wrapped_report_class = fingerprint_details


