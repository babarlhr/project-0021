from datetime import datetime
import pytz
import time
from openerp import tools
from openerp.osv import osv
from openerp.report import report_sxw

class absence_summary(report_sxw.rml_parse):

    def _get_employees(self, ids):
        employee_obj = self.pool.get('hr.employee')
        return employee_obj.search(self.cr, self.uid, ids)

    def _get_employee(self, employee_id):
        employee_obj = self.pool.get('hr.employee')
        return employee_obj.browse(self.cr, self.uid, employee_id)

    def __init__(self, cr, uid, name, context):
        super(absence_summary, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'datetime': datetime,
            'get_employees': self._get_employees,
            'get_employee': self._get_employee,
        })


class report_absence_summary(osv.AbstractModel):
    _name = 'report.jakc_hr_schedule.report_absencesummary'
    _inherit = 'report.abstract_report'
    _template = 'jakc_hr_schedule.report_absencesummary'
    _wrapped_report_class = absence_summary


