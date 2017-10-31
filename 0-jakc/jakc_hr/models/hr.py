from openerp import fields, models, api, _
from openerp.exceptions import Warning
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    nik = fields.Char('Nik', size=10, required=True)
    _sql_constraints = [
        (
        'uniq_nik', 'unique(nik)', "A NIK already exist. NIK name must be unique!"),
    ]

class HrDepartment(models.Model):
    _inherit = 'hr.department'

    dept_code = fields.Char('Dept Code', size=10, required=True)

    _sql_constraints = [
        ('uniq_dept_code', 'unique(dept_code)', "A Department Code already exist. Department Code name must be unique!"),
    ]