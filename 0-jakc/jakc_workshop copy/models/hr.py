from openerp import fields, models, api, _
from openerp.exceptions import Warning
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    nik = fields.Char('Nik', size=10, required=True)