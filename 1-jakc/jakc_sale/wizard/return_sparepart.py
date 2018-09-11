from openerp import models, fields, api, _
from openerp.exceptions import ValidationError, UserError, Warning
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class WizardReturnSparepart(models.TransientModel):
    _name = 'wizard.return.sparepart'

    @api.model
    def default_get(self, fields):
        res = super(WizardReturnSparepart, self).default_get(fields)
        sale_order_sparepart_obj = self.env['sale.order.sparepart']
        active_id = self.env.context.get('active_id') or False
        sale_order_sparepart = sale_order_sparepart_obj.browse(active_id)
        res['back_order_id'] = sale_order_sparepart.id
        res['product_id'] = sale_order_sparepart.product_id.id
        res['product_uom_qty'] = sale_order_sparepart.product_uom_qty
        res['product_uom'] = sale_order_sparepart.product_uom.id
        res['sparepart_flow'] = 'return'
        if  sale_order_sparepart.sparepart_flow  == 'out':
            res['order_line_id'] = sale_order_sparepart.order_line_id.id
        else:
            res['sparepart_line_id'] = sale_order_sparepart.sparepart_line_id.id
        return res

    back_order_id = fields.Many2one('sale.order.sparepart', 'Sparepart', readonly=True)
    product_id = fields.Many2one('product.product', 'Product', required=True)
    product_uom_qty = fields.Float('Quantity', required=True)
    product_uom = fields.Many2one('product.uom', 'Unit of Measure', required=True)
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True, readonly=False)
    type = fields.Selection([('order', 'Order Line'), ('insurance', 'Insurance')], 'Type', readonly=True)
    sparepart_flow = fields.Selection([('in', 'Incoming'), ('out', 'Outgoing'), ('return', 'Return')], 'Flow')
    order_line_id = fields.Many2one('sale.order.line', 'Order Line', readonly=True)
    sparepart_line_id = fields.Many2one('sale.order.sparepart.line', 'Sparepart Line', readonly=True)

    @api.one
    def process_sparepart(self):
        sale_order_sparepart_obj = self.env['sale.order.sparepart']
        stock_move_obj = self.env['stock.move']
        company_id = self.env.user.company_id
        active_id = self.env.context.get('active_id') or False
        sale_order_sparepart = sale_order_sparepart_obj.browse(active_id)

        #Create Return Sale Order Sparepart
        if sale_order_sparepart.sparepart_flow == 'out':
            sparepart = {}

        if sale_order_sparepart.sparepart_flow == 'in':
            #Create Sparepart
            logger.info("Insurance")
            sparepart = {}
            sparepart.update({'back_order_id': self.back_order_id.id})
            sparepart.update({'product_id': sale_order_sparepart.product_id.id})
            sparepart.update({'sale_order_id': sale_order_sparepart.sale_order_id.id})
            sparepart.update({'type': 'insurance'})
            sparepart.update({'sparepart_flow': 'return'})
            sparepart.update({'sparepart_line_id': sale_order_sparepart.sparepart_line_id.id})
            sparepart.update({'product_uom_qty': sale_order_sparepart.product_uom.id})
            sparepart.update({'product_uom': sale_order_sparepart.product_uom.id})
            args = [('product_id', '=', sparepart.get('product_id')),
                    ('sparepart_flow', '=', 'return'),
                    ('sparepart_line_id', '=', sparepart.get('sparepart_line_id'))]
            part = sale_order_sparepart_obj.search(args)
            logger.info(part)
            if not part:
                logger.info("Part")
                result = sale_order_sparepart_obj.create(sparepart)
                if result:
                    logger.info(result)
                    #Create Stock Move
                    vals = {}
                    # vals.update({'picking_id': stock_picking.id})
                    vals.update({'name': 'Insurance Sparepart'})
                    vals.update({'date': datetime.today()})
                    vals.update({'date_expected': datetime.today()})
                    vals.update({'product_id': sale_order_sparepart.product_id.id})
                    vals.update({'product_uom_qty': sale_order_sparepart.product_uom_qty})
                    vals.update({'product_uom': sale_order_sparepart.product_uom.id})
                    vals.update({'location_id': company_id.insurance_location_dest_id.id})
                    vals.update({'location_dest_id': company_id.insurance_location_src_id.id})
                    vals.update({'procure_method': 'make_to_stock'})
                    vals.update({'origin': sale_order_sparepart.sale_order_id.name})
                    stock_move = stock_move_obj.create(vals)
                    logger.info("Create Stock Move")
                    stock_move.action_done()
                    result.stock_move_id = stock_move.id
                else:
                    raise ValidationError("Error Sale Sparepart Order")
