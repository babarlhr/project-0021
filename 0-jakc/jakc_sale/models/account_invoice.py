from datetime import datetime, timedelta
from openerp import SUPERUSER_ID
from openerp import api, fields, models, _
import openerp.addons.decimal_precision as dp
from openerp.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
import logging

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    sale_order_id = fields.Many2one('sale.order', 'Order #', readonly=True)
    iface_or_invoice = fields.Boolean('Is OR', default=False)