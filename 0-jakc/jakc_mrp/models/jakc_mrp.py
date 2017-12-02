from openerp import fields, models, api, _
from openerp.exceptions import Warning
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    @api.one
    def _calculate_bom_cost(self):
        total = 0
        for line in self.bom_line_ids:
            total += (line.product_id.list_price * line.product_qty)

        self.bom_cost = total

    bom_cost = fields.Float(string='Bom Cost', compute='_calculate_bom_cost')
    list_price = fields.Float(string='Price', related='product_id.list_price')
