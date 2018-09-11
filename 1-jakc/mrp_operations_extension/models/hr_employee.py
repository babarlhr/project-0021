from openerp import fields, models, api, _
from openerp.exceptions import Warning
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    production_workcenter_line_ids = fields.One2many('mrp.production.workcenter.operators','operator_id','Production Workorders', readonly=True)
