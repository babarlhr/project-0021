from openerp import fields, models, api, _
from openerp.exceptions import Warning, ValidationError
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)



class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    nik = fields.Char('NIK', size=20, required=True)
