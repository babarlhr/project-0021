from openerp import models, fields, api, _, exceptions
from datetime import datetime

import logging

logger = logging.getLogger(__name__)

class WizardAddMaterial(models.TransientModel):
    _name = 'wizard.add.material'

    @api.onchange('product_id')
    def product_id_change(self):
        logger.debug("Change Product")
        self.product_uom = self.product_id.uom_id.id
        need_approval = self._check_approval_need()

    @api.onchange('product_qty')
    def product_qty_change(self):
        need_approval = self._check_approval_need()


    @api.one
    def _check_approval_need(self):
        sale_order_consume_material_obj = self.env['sale.order.consume.material']

        active_id = self.env.context.get('active_id') or False
        consume_material = sale_order_consume_material_obj.browse(active_id)

        amount_total = consume_material.sale_order_id.amount_total
        material_amount = consume_material.sale_order_id.scheduled_product_amount
        standard_price = self.product_qty * self.product_id.standard_price

        estimate_percentage = (material_amount + standard_price) / amount_total * 100
        if estimate_percentage > 25:
            return True
        else:
            return False

    product_id = fields.Many2one('product.product', 'Product', readonly=True, required=True)
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True)
    product_qty = fields.Float('Product Quantity', required=True, default=1)
    product_uom = fields.Many2one('product.uom', 'Product Unit of Measure', required=True)

    @api.model
    def default_get(self, fields):
        res = super(WizardAddMaterial, self).default_get(fields)
        sale_order_consume_material_obj = self.env['sale.order.consume.material']
        active_id = self.env.context.get('active_id') or False
        sale_order_consume_material = sale_order_consume_material_obj.browse(active_id)
        if sale_order_consume_material:
            res['product_id'] = sale_order_consume_material.product_id.id
        return res

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
        sale_order_add_material_obj = self.env['sale.order.add.material']
        sale_order_add_material_Line_obj = self.env['sale.order.add.material.line']
        sale_order_consume_material_obj = self.env['sale.order.consume.material']

        active_id = self.env.context.get('active_id') or False
        consume_material = sale_order_consume_material_obj.browse(active_id)

        if consume_material.quantity_done == 0:
            raise exceptions.Warning(_('Please Claim Material Before Add Material'))
        else:
            amount_total = consume_material.sale_order_id.sale_workorder_amount
            material_amount = consume_material.sale_order_id.scheduled_product_amount
            standard_price = self.product_qty * self.product_id.standard_price

            estimate_percentage = (material_amount + standard_price) / amount_total * 100
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