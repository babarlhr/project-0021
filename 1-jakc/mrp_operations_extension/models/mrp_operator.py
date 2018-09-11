from openerp import fields, models, api, _
from openerp.exceptions import Warning
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class MrpProductionWorkcenterOperator(models.Model):
    _name = 'mrp.production.workcenter.operators'

    production_workcenter_line_id = fields.Many2one('mrp.production.workcenter.line', 'Production Workorder')
    operator_id = fields.Many2one('hr.employee', 'Operator', required=True)
    work_date = fields.Date('Work Date', required=True)

