from datetime import datetime, timedelta
from openerp import SUPERUSER_ID
from openerp import api, fields, models, _
import openerp.addons.decimal_precision as dp
from openerp.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
import logging


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    sparepart_id = fields.Many2one('sale.order.sparepart','Sparepart #')
    sparepart_line_id = fields.Many2one('sale.order.sparepart.line', 'Sparepar Line #')
    mechanic_id = fields.Many2one('hr.employee','Mechanic')


class StockMove(models.Model):
    _inherit = 'stock.move'

    sale_order_id = fields.Many2one(comodel_name='sale.order', string='Order #', store=True, related='production_id.sale_order_id')
    #sale_order_id = fields.Many2one('saler.order','Sale Order #')
    sparepart_line_id = fields.Many2one('sale.order.sparepart.line', 'Sparepar Line #', index=True)
    #sparepart_flow_type = fields.Selection([('in','Incoming'),('out','Outgoing')],'Flow Type', index=True)
    pickup_by = fields.Many2one('hr.employee', 'Mechanic', index=True)

    @api.multi
    def move_consume_2(self):
        print "Move Consume 2"
        move = self
        move_obj = self.env['stock.move']
        uom_obj = self.env['product.uom']
        production_obj = self.env['mrp.production']
        production_id = move.raw_material_production_id.id
        production = production_obj.browse(production_id)
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        qty = uom_obj._compute_qty(move.product_uom.id, move.product_uom_qty, move.product_id.uom_id.id)
        remaining_qty = move.product_uom_qty - qty
        #remaining_qty = move.product_uom_qty - qty

        if float_compare(remaining_qty, 0, precision_digits=precision) >= 0:
            move_obj.action_consume([move.id], qty, move.location_id.id)
            logger.info("Action Consume 1")
        else:
            consumed_qty = min(move.product_qty, qty)
            new_moves = move_obj.action_consume([move.id], consumed_qty, move.location_id.id )
            # consumed more in wizard than previously planned
            extra_more_qty = qty - consumed_qty
            # create new line for a remaining qty of the product
            extra_move_id = production_obj._make_consume_line_from_data(production, move.product_id,
                                                                        move.product_id.uom_id.id, extra_more_qty)
            move_obj.write([extra_move_id], {'restrict_lot_id': move.restrict_lot_id.id})
            move_obj.action_done([extra_move_id])
            logger.info("Action Consume 2")
