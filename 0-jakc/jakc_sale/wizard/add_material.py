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

    product_id = fields.Many2one('product.product', 'Product', required=True)
    product_qty = fields.Float('Product Quantity', required=True)
    product_uom = fields.Many2one('product.uom', 'Product Unit of Measure', required=True)


    @api.one
    def add_material(self):
        production_obj = self.env['mrp.production']
        stock_move_obj = self.env['stock.move']
        workcenter_line_obj = self.env['mrp.production.workcenter.line']
        procurement_order_obj = self.env['procurement.order']

        active_id = self.env.context.get('active_id') or False
        workcenter_line = workcenter_line_obj.browse(active_id)

        amount_total = workcenter_line.production_id.sale_order_id.amount_total
        material_amount = workcenter_line.production_id.sale_order_id.scheduled_product_amount
        standard_price = self.product_qty * self.product_id.standard_price

        estimate_percentage = (material_amount + standard_price) / amount_total * 100
        if estimate_percentage > 25:
            raise exceptions.ValidationError(_("Material Amount Exceeded!"))

        values = {}
        values.update({'name': self.product_id.name})
        values.update({'production_id': workcenter_line.production_id.id})
        values.update({'product_id': self.product_id.id})
        values.update({'product_qty': self.product_qty})
        values.update({'product_uom': self.product_uom.id})
        values.update({'work_order': workcenter_line.routing_wc_line.id})
        res = self.env['mrp.production.product.line'].create(values)
        stock_move_id = production_obj._make_production_consume_line(res)
        if stock_move_id:
            stock_move = stock_move_obj.browse(stock_move_id)
            #self.env['stock.move'].action_confirm([stock_move_id])
            #self.stock_move_action_confirm(stock_move_id)
            stock_move.action_confirm()
            logger.info("Stock Move Action Confirm")
            procurement_order_obj.run_scheduler()
        else:
            logger.info("Stock Move Action Confirm Failed")


class WizardReturnMaterial(models.TransientModel):
    _name = 'wizard.return.material'

    @api.onchange('product_id')
    def product_id_change(self):
        logger.debug("Change Product")
        self.product_uom = self.product_id.uom_id.id


    product_id = fields.Many2one('product.product', 'Product', readonly=True)
    quantity = fields.Float('Quantity', readonly=True)
    quantity_done = fields.Float('Claim', readonly=True)
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
            res['quantity'] = sale_order_consume_material.quantity
            res['quantity_done'] = sale_order_consume_material.quantity_done
            res['product_qty'] = sale_order_consume_material.quantity_done
        return res

    @api.multi
    def _make_stock_return(self):
        stock_move_obj = self.env['stock.move']
        loc_obj = self.env['stock.location']
        stock_picking = self.sale_order_id.sparepart_stock_picking_id

        for line in self:
            # Take routing location as a Source Location.
            vals = {}
            vals.update({'picking_id': stock_picking.id})
            vals.update({'name': line.sale_order_id.name})
            vals.update({'date': datetime.today()})
            vals.update({'date_expected': line.expected_date})
            vals.update({'product_id': line.product_id.id})
            vals.update({'product_uom_qty': line.product_uom_qty})
            vals.update({'product_uom': line.product_uom.id})
            vals.update({'location_id': stock_picking.location_id.id})
            vals.update({'location_dest_id': stock_picking.location_dest_id.id})
            # vals.update({'company_id': line.})
            vals.update({'procure_method': 'make_to_stock'})
            vals.update({'origin': line.sale_order_id.name})
            stock_move = stock_move_obj.create(vals)
            stock_move.action_confirm()
            line.stock_move_id = stock_move.id
        return stock_move

    @api.one
    def return_material(self):
        production_obj = self.env['mrp.production']
        stock_move_obj = self.env['stock.move']
        workcenter_line_obj = self.env['mrp.production.workcenter.line']
        sale_order_consume_material_obj = self.env['sale.order.consume.material']
        active_id = self.env.context.get('active_id') or False
        sale_order_consume_material = sale_order_consume_material_obj.browse(active_id)
        rest_qty = self.product_qty
        for line in sale_order_consume_material.line_ids:
            product_qty = line.stock_move_id.product_qty
            if rest_qty > product_qty:
                rest_qty = self.product_qty - product_qty
                curr_qty = product_qty
            else:
                rest_qty = 0
                curr_qty = self.product_qty

            vals = {}
            vals.update({'production_id': line.stock_move_id.raw_material_production_id.id})
            vals.update({'name': line.stock_move_id.raw_material_production_id.name})
            vals.update({'date': datetime.today()})
            #vals.update({'date_expected': lines.expected_date})
            vals.update({'product_id': self.product_id.id})
            vals.update({'product_uom_qty': curr_qty})
            vals.update({'product_uom': self.product_uom.id})
            vals.update({'location_id': 7})
            vals.update({'location_dest_id': 18})
            # vals.update({'company_id': line.})
            #vals.update({'procure_method': 'make_to_stock'})
            vals.update({'origin': line.stock_move_id.raw_material_production_id.name})
            stock_move = stock_move_obj.create(vals)
            stock_move.action_confirm()
            logger.info("Stock Move Created : " + str(stock_move.id))
            #stock_move_id = stock_move.id

            #values = {}
            #values.update({'name': self.product_id.name})
            #values.update({'production_id': line.stock_move_id.raw_material_production_id.id})
            #values.update({'product_id': self.product_id.id})
            #values.update({'product_qty': -1 * curr_qty})
            #values.update({'product_uom': self.product_uom.id})
            #values.update({'work_order': line.stock_move_id.work_order.id})
            #res = self.env['mrp.production.product.line'].create(values)
            #stock_move_id = production_obj._make_production_consume_line(res)
            #if stock_move_id:
            #    stock_move = stock_move_obj.browse(stock_move_id)
            #    # self.env['stock.move'].action_confirm([stock_move_id])
            #    # self.stock_move_action_confirm(stock_move_id)
            #    stock_move.action_confirm()

            if rest_qty == 0:
                break