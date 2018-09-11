from openerp import models, fields, api
from datetime import datetime

class WizardConsumeMaterial(models.TransientModel):
    _name = 'wizard.consume.material'

    @api.model
    def default_get(self, fields):
        res = super(WizardConsumeMaterial, self).default_get(fields)
        sale_order_consume_material_obj = self.env['sale.order.consume.material']
        active_id = self.env.context.get('active_id') or False
        sale_order_consume_material = sale_order_consume_material_obj.browse(active_id)
        res['consume_material_id'] = sale_order_consume_material.id
        res['product_id'] = sale_order_consume_material.product_id.id
        res['qty'] = sale_order_consume_material.quantity
        return res

    consume_material_id = fields.Many2one('sale.order.consume.material', 'Consume Material', readonly=True)
    product_id = fields.Many2one('product.product','Product', readonly=True)
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True)
    qty = fields.Float('Claim Qty', required=True)

    @api.one
    def do_move_consume(self, cr, uid, ids, context=None):

        move_obj = self.env['stock.move']
        uom_obj = self.env['product.uom']
        production_obj = self.env['mrp.production']
        move_ids = context['active_ids']
        move = move_obj.browse(cr, uid, move_ids[0], context=context)
        production_id = move.raw_material_production_id.id
        production = production_obj.browse(cr, uid, production_id, context=context)
        precision = self.pool['decimal.precision'].precision_get(cr, uid, 'Product Unit of Measure')

        for data in self.browse(cr, uid, ids, context=context):
            qty = uom_obj._compute_qty(cr, uid, data['product_uom'].id, data.product_qty, data.product_id.uom_id.id)
            remaining_qty = move.product_qty - qty
            # check for product quantity is less than previously planned
            if float_compare(remaining_qty, 0, precision_digits=precision) >= 0:
                move_obj.action_consume(cr, uid, move_ids, qty, data.location_id.id,
                                        restrict_lot_id=data.restrict_lot_id.id, context=context)
            else:
                consumed_qty = min(move.product_qty, qty)
                new_moves = move_obj.action_consume(cr, uid, move_ids, consumed_qty, data.location_id.id,
                                                    restrict_lot_id=data.restrict_lot_id.id, context=context)
                # consumed more in wizard than previously planned
                extra_more_qty = qty - consumed_qty
                # create new line for a remaining qty of the product
                extra_move_id = production_obj._make_consume_line_from_data(cr, uid, production, data.product_id,
                                                                            data.product_id.uom_id.id, extra_more_qty,
                                                                            context=context)
                move_obj.write(cr, uid, [extra_move_id], {'restrict_lot_id': data.restrict_lot_id.id}, context=context)
                move_obj.action_done(cr, uid, [extra_move_id], context=context)

    @api.one
    def process_consume_material(self):
        consume_material_id = self.consume_material_id
        consume_material_id.employee_id = self.employee_id.id
        consume_material_id.trans_consume_material()
        self.consume_material_id.sale_order_id.trans_merge_stock_move()
