from datetime import datetime, timedelta
from openerp import SUPERUSER_ID
from openerp import api, fields, models, _
import openerp.addons.decimal_precision as dp
from openerp.exceptions import UserError
from openerp.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
import logging


class ResCompany(models.Model):
    _inherit = 'res.company'

    routing_wc = fields.Many2one('mrp.routing', 'Routing')
    or_product = fields.Many2one('product.product', 'OR')
