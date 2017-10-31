# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp import api, fields, models, _, SUPERUSER_ID
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.translate import _
from openerp.tools.float_utils import float_is_zero, float_compare
import openerp.addons.decimal_precision as dp
from openerp.exceptions import UserError, AccessError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order.line'

    iface_workorder_purchase = fields.Boolean('Is Workorder', default=False)
    sale_order_id = fields.Many2one('sale.order','Sale Order #', readonly=True)
    sale_order_line_id = fields.Many2one('sale.order.line', 'Sale Order Line #', readonly=True)
