import time

from openerp import api, fields, models, _
import openerp.addons.decimal_precision as dp
from openerp.tools import float_compare
from openerp.exceptions import UserError

class StockMoveConsume(models.TransientModel):
    _inherit = 'stock.move.consume'

    @api.model
    def default_get(self, fields):
        res = super(StockMoveConsume, self).default_get(fields)
        active_id = self.env.context.get('active_id') or False
        move = self.env['stock.move'].browse(active_id)
        if 'product_id' in fields:
            res.update({'product_id': move.product_id.id})
        if 'product_uom' in fields:
            res.update({'product_uom': move.product_uom.id})
        if 'product_qty' in fields:
            res.update({'product_qty': move.product_uom_qty})
            res.update({'product_bom_qty': move.product_uom_qty})
        if 'location_id' in fields:
            res.update({'location_id': move.location_id.id})
        return res

    @api.one
    @api.onchange('product_qty')
    def on_change_product_qty(self):
        self.product_diff = self.product_bom_qty - self.product_qty

    product_bom_qty = fields.Float('Bom Qty', digits_compute=dp.get_precision('Product Unit of Measure'), readonly=True)
    product_diff = fields.Float('Different', digits_compute=dp.get_precision('Product Unit of Measure'), default=0.0, readonly=True)


    @api.one
    def add_material(self):
        production_obj = self.env['mrp.production']
        stock_move_obj = self.env['stock.move']
        workcenter_line_obj = self.env['mrp.production.workcenter.line']

        active_id = self.env.context.get('active_id') or False
        workcenter_line = workcenter_line_obj.browse(active_id)

        values = {}
        values.update({'name': self.product_id.name})
        values.update({'production_id': workcenter_line.production_id.id})
        values.update({'product_id': self.product_id.id})
        values.update({'product_qty': self.product_diff})
        values.update({'product_uom': self.product_uom.id})
        values.update({'work_order': workcenter_line.routing_wc_line.id})
        res = self.env['mrp.production.product.line'].create(values)
        stock_move_id = production_obj._make_production_consume_line(res)
        if stock_move_id:
            stock_move = stock_move_obj.browse(stock_move_id)
            #self.env['stock.move'].action_confirm([stock_move_id])
            #self.stock_move_action_confirm(stock_move_id)
            stock_move.action_confirm()

    @api.multi
    def do_move_consume(self):
        if self.product_diff > 0:
            print "Product diff"
            self.add_material(self)
        return super(StockMoveConsume, self).do_move_consume()




