from openerp import models, fields, api
from datetime import datetime


class WizardConsumeMaterial(models.TransientModel):
    _name = 'wizard.consume.material'

    @api.one
    def _get_stock(self):
        ### get recordset of related object, for example with search (or whatever you like):
        line_ids= []
        sale_order_obj = self.env['sale.order']
        active_ids = self.env.context.get('active_ids') or False
        sale_order = sale_order_obj.browse(active_ids[0])
        for production in sale_order.production_ids:
            for move_line in production.move_lines:
                line = {}
                line.update({'product_id': move_line.product_id.id})
                line.update({'product_qty': move_line.product_uom_qty})
                res = self.env['wizard.consume.material.line'].create(line)
                line_ids.append(res)
        self.consume_material_line_ids = line_ids

    #@api.model
    #def default_get(self, fields_list):
    #    a = super(WizardConsumeMaterial, self).default_get(fields_list)
    #    stock_moves = []
    #    sale_order_obj = self.env['sale.order']
    #    stock_move_obj = self.env['stock.move']
    #    active_ids = self.env.context.get('active_ids') or False
    #    args = [('sale_order_id','=', active_ids[0])]
    #    stock_move_ids = stock_move_obj.search(args)
        #for stock_move_id in stock_move_ids:
        #    stock_move_id.update({'consume_material_id': self.id})
        #    stock_moves.append(stock_move_id)
    #    a.update({'stock_move_ids' : stock_move_ids})
    #    return a

    @api.onchange('mrp_routing_workcenter_id')
    def onchange_mrp_routing_workcenter_id(self):
        sale_order_obj = self.env['sale.order']
        stock_move_obj = self.env['stock.move']
        stock_move_ids = []
        active_ids = self.env.context.get('active_ids') or False
        args = [('sale_order_id','=', active_ids[0])]
        stock_moves = stock_move_obj.search(args)
        for stock_move in stock_moves:
            stock_move_ids.append(stock_move.id)
        self.stock_move_ids = stock_move_ids

    mrp_routing_id = fields.Many2one('mrp.routing', 'Routing', required=True)
    mrp_routing_workcenter_id  = fields.Many2one('mrp.routing.workcenter', 'Workcenter', required=True)
    stock_move_ids = fields.One2many('stock.move', 'consume_material_id', string='Stock Move')

class WizardCosumeMaterialLine(models.TransientModel):
    _inherit = 'stock.move'

    consume_material_id = fields.Many2one('wizard.consume.material', 'Consume #')