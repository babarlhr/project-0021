from datetime import datetime, timedelta
from openerp import SUPERUSER_ID
from openerp import api, fields, models, _
import openerp.addons.decimal_precision as dp
from openerp.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
import logging


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ProcurementOrder(models.Model):
    _inherit = ['procurement.order']

    sale_order_id = fields.Many2one('sale.order','Sale Order', related='sale_line_id.order_id', readonly=True)
    partner_vehicle_id = fields.Many2one('partner.vehicle', related='sale_order_id.partner_vehicle_id', readonly=True, string='Vehicle')

