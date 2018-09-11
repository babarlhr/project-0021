from openerp import models, fields, api, _, exceptions
from datetime import datetime

import logging

logger = logging.getLogger(__name__)


class WizardAddOrderLine(models.TransientModel):
    _name = 'wizard.add.order.line'

    @api.model
    def default_get(self, fields):
        res = super(WizardAddOrderLine, self).default_get(fields)
        active_id = self.env.context.get('active_id') or False
        res['sale_order_id'] = active_id
        return res

    @api.onchange('product_id')
    def product_id_change(self):
        logger.debug("Change Product")
        self.product_uom = self.product_id.uom_id.id

    sale_order_id = fields.Many2one('sale.order', 'Sale Order', readonly=True)
    product_id = fields.Many2one('product.product', 'Product', required=True)
    product_uom_qty = fields.Float('Product Quantity', required=True, default=1)
    product_uom = fields.Many2one('product.uom', 'Product Unit of Measure', required=True)

    @api.multi
    def add_order_line(self):
        line_env = self.env['sale.order.line']
        new_line = line_env.create({
            'order_id': self.sale_order_id.id,
            'product_id': self.product_id.id,
            'iface_sparepart': True,
            'name': self.product_id.name,
            'order_id': self.sale_order_id.id,
            'product_uom_qty' : self.product_uom_qty,
            'product_uom': self.product_id.uom_id.id,
            })
        new_line.product_id_change()