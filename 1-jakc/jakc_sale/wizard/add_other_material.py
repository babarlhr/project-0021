from openerp import models, fields, api, _, exceptions
from datetime import datetime

import logging

logger = logging.getLogger(__name__)


class WizardAddOtherMaterial(models.TransientModel):
    _name = 'wizard.add.other.material'

    @api.model
    def default_get(self, fields):
        res = super(WizardAddOtherMaterial, self).default_get(fields)
        company_id  = self.env.user.company_id
        res['domain'] = {'product_id': [('categ_id', '=',company_id.material_product_category_id.id)]}
        return res

    @api.onchange('product_id')
    def product_id_change(self):
        logger.debug("Change Product")
        self.product_uom = self.product_id.uom_id.id

    product_id = fields.Many2one('product.product', 'Product', readonly=False, required=True)
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True)
    product_qty = fields.Float('Product Quantity', required=True, default=1)
    product_uom = fields.Many2one('product.uom', 'Product Unit of Measure', required=True)

    @api.one
    def _make_stock_move_request(self, add_material):
        stock_move_obj = self.env['stock.move']
        stock_move = stock_move_obj.create({
            'name': add_material.sale_order_id.name,
            'product_id': add_material.product_id.id,
            'restrict_lot_id': False,
            'product_uom_qty': self.product_qty,
            'product_uom': add_material.product_uom.id,
            'partner_id': add_material.sale_order_id.partner_id.id,
            'location_id': 18,
            'location_dest_id': 7,
        })
        return stock_move

    @api.one
    def _make_stock_move(self, add_material):
        stock_move_obj = self.env['stock.move']
        stock_move = stock_move_obj.create({
            'name': add_material.sale_order_id.name,
            'product_id': add_material.product_id.id,
            'restrict_lot_id': False,
            'product_uom_qty': self.product_qty,
            'product_uom': add_material.product_uom.id,
            'partner_id': add_material.sale_order_id.partner_id.id,
            'location_id': 18,
            'location_dest_id': 7,
        })
        stock_move.action_done()
        return stock_move

    @api.one
    def add_material(self):
        sale_order_obj = self.env['sale.order']
        sale_order_add_material_obj = self.env['sale.order.add.material']
        sale_order_add_material_Line_obj = self.env['sale.order.add.material.line']
        sale_order_consume_material_obj = self.env['sale.order.consume.material']

        active_id = self.env.context.get('active_id') or False
        sale_order = sale_order_obj.browse(active_id)
        consume_material_ids = sale_order_consume_material_obj.search([('sale_order_id','=', sale_order.id),('product_id','=', self.product_id.id)])

        if not consume_material_ids:
            consume_material_values = {}
            consume_material_values.update({'sale_order_id': sale_order.id})
            consume_material_values.update({'product_id': self.product_id.id})
            consume_material = sale_order_consume_material_obj.create(consume_material_values)
        else:
            consume_material = consume_material_ids[0]

        amount_total = consume_material.sale_order_id.amount_untaxed
        material_amount = consume_material.sale_order_id.scheduled_product_amount
        standard_price = self.product_qty * self.product_id.standard_price

        estimate_percentage = (material_amount + standard_price) / amount_total * 100
        logging.info(estimate_percentage)
        if estimate_percentage > 25:
            values = {}
            values.update({'sale_order_id': consume_material.sale_order_id.id})
            values.update({'product_id': self.product_id.id})
            values.update({'employee_id': self.employee_id.id})
            values.update({'product_uom_qty': self.product_qty})
            values.update({'product_uom': self.product_uom.id})
            values.update({'state': 'request'})
            result = sale_order_add_material_obj.create(values)
            stock_move = self._make_stock_move_request(result)[0]
            result.stock_move_id = stock_move.id
        else:
            values = {}
            values.update({'sale_order_id': consume_material.sale_order_id.id})
            values.update({'product_id': self.product_id.id})
            values.update({'employee_id': self.employee_id.id})
            values.update({'product_uom_qty': self.product_qty})
            values.update({'product_uom': self.product_uom.id})
            values.update({'state': 'done'})
            result = sale_order_add_material_obj.create(values)
            stock_move = self._make_stock_move(result)[0]
            result.stock_move_id = stock_move.id

        consume_material.sale_order_id.trans_merge_stock_move()
        consume_material.sale_order_id.message_post(body=_("""Add Material {} for {} {} """.format(self.product_id.name, self.product_qty, self.product_uom.name)))