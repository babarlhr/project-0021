# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def _make_production_consume_line(self, cr, uid, line, context=None):
        return self._make_consume_line_from_data(cr, uid,
                                                 line.production_id,
                                                 line.product_id,
                                                 line.product_uom.id,
                                                 line.product_qty,
                                                 line.addition,
                                                 line.deduction,
                                                 context=context)

    def _make_consume_line_from_data(self, cr, uid, production, product, uom_id, qty, addition, deduction, context=None):
        stock_move = self.pool.get('stock.move')
        loc_obj = self.pool.get('stock.location')
        # Internal shipment is created for Stockable and Consumer Products
        if product.type not in ('product', 'consu'):
            return False
        # Take routing location as a Source Location.
        source_location_id = production.location_src_id.id
        prod_location_id = source_location_id
        prev_move = False
        if production.routing_id:
            routing = production.routing_id
        else:
            routing = production.bom_id.routing_id

        if routing and routing.location_id and routing.location_id.id != source_location_id:
            source_location_id = routing.location_id.id
            prev_move = True

        destination_location_id = production.product_id.property_stock_production.id


        move_id = stock_move.create(cr, uid, {
            'name': production.name,
            'date': production.date_planned,
            'date_expected': production.date_planned,
            'product_id': product.id,
            'product_uom_qty': qty,
            'product_uom': uom_id,
            'location_id': source_location_id if addition else destination_location_id ,
            'location_dest_id': destination_location_id if addition else source_location_id,
            'company_id': production.company_id.id,
            'procure_method': prev_move and 'make_to_stock' or self._get_raw_material_procure_method(cr, uid, product,
                                                                                                     location_id=source_location_id,
                                                                                                     location_dest_id=destination_location_id,
                                                                                                     context=context),
        # Make_to_stock avoids creating procurement
            'raw_material_production_id': production.id,
            # this saves us a browse in create()
            'price_unit': product.standard_price,
            'origin': production.name,
            'warehouse_id': loc_obj.get_warehouse(cr, uid, production.location_src_id, context=context),
            'group_id': production.move_prod_id.group_id.id,
        }, context=context)

        if prev_move:
            prev_move = self._create_previous_move(cr, uid, move_id, product, prod_location_id, source_location_id,
                                                   context=context)
            stock_move.action_confirm(cr, uid, [prev_move], context=context)

        if 'work_order' in self.env.context:
            move_obj = self.env['stock.move']
            work_order = self.env.context.get('work_order')
            picking_type = work_order.routing_wc_line.picking_type_id
            if picking_type:
                vals = {
                    'location_id': picking_type.default_location_src_id.id,
                    'location_dest_id': (picking_type.default_location_dest_id.id)}
                move_obj.browse(move_id).write(vals)

        return move_id

    @api.model
    def _make_consume_line_from_data_1(self, production, product, uom_id, qty, uos_id, uos_qty):
        move_id = super(MrpProduction, self)._make_consume_line_from_data(
            production, product, uom_id, qty, uos_id, uos_qty)
        if 'work_order' in self.env.context:
            move_obj = self.env['stock.move']
            work_order = self.env.context.get('work_order')
            picking_type = work_order.routing_wc_line.picking_type_id
            if picking_type:
                vals = {
                    'location_id': picking_type.default_location_src_id.id,
                    'location_dest_id': (
                        picking_type.default_location_dest_id.id)}
                move_obj.browse(move_id).write(vals)
        return move_id
