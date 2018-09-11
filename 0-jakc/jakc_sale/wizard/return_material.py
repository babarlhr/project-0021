from openerp import models, fields, api, _, exceptions
from datetime import datetime

import logging

logger = logging.getLogger(__name__)


class WizardReturnMaterial(models.TransientModel):
    _name = 'wizard.return.material'

    @api.onchange('product_id')
    def product_id_change(self):
        logger.debug("Change Product")
        self.product_uom = self.product_id.uom_id.id

    product_id = fields.Many2one('product.product', 'Product', readonly=True)
    employee_id = fields.Many2one('hr.employee','Employee', required=True)
    product_qty = fields.Float('Product Quantity', required=True)
    product_uom = fields.Many2one('product.uom', 'Product Unit of Measure', required=True)

    @api.model
    def default_get(self, fields):
        res = super(WizardReturnMaterial, self).default_get(fields)
        sale_order_consume_material_obj = self.env['sale.order.consume.material']
        active_id = self.env.context.get('active_id') or False
        sale_order_consume_material = sale_order_consume_material_obj.browse(active_id)
        if sale_order_consume_material:
            res['product_id'] = sale_order_consume_material.product_id.id
        return res

    @api.one
    def _make_stock_move(self, return_material):
        stock_move_obj = self.env['stock.move']
        stock_move = stock_move_obj.create({
            'name': return_material.sale_order_id.name,
            'product_id': return_material.product_id.id,
            'restrict_lot_id': False,
            'product_uom_qty': self.product_qty,
            'product_uom': return_material.product_uom.id,
            'partner_id': return_material.sale_order_id.partner_id.id,
            'location_id': 7,
            'location_dest_id': 18,
        })
        stock_move.action_done()
        return stock_move

    @api.one
    def return_material(self):
        sale_order_return_material_obj = self.env['sale.order.return.material']
        sale_order_return_material_Line_obj = self.env['sale.order.return.material.line']
        sale_order_consume_material_obj = self.env['sale.order.consume.material']

        active_id = self.env.context.get('active_id') or False
        consume_material = sale_order_consume_material_obj.browse(active_id)

        if consume_material.quantity_done == 0:
            raise exceptions.ValidationError(_('Please Claim Material Before Return Material'))
        elif consume_material.quantity < self.product_qty:
            raise exceptions.ValidationError(_('Quantity Over for Return Material'))
        else:
            values = {}
            values.update({'sale_order_id': consume_material.sale_order_id.id})
            values.update({'product_id': self.product_id.id})
            values.update({'employee_id': self.employee_id.id})
            values.update({'product_uom_qty': self.product_qty})
            values.update({'product_uom': self.product_uom.id})
            result = sale_order_return_material_obj.create(values)
            stock_move = self._make_stock_move(result)[0]
            result.stock_move_id = stock_move.id


        consume_material.sale_order_id.trans_merge_stock_move()