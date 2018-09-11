from openerp import models, fields, api
from datetime import datetime
from openerp.exceptions import ValidationError, Warning, UserError
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class WizardProcessProductionSparepart(models.TransientModel):
    _name = 'wizard.process.production.sparepart'

    @api.model
    def default_get(self, fields):
        res = super(WizardProcessProductionSparepart, self).default_get(fields)
        sale_order_sparepart_obj = self.env['sale.order.sparepart']
        active_id = self.env.context.get('active_id') or False
        sale_order_sparepart = sale_order_sparepart_obj.browse(active_id)
        res['sparepart_id'] = sale_order_sparepart.id
        res['employee_id'] = sale_order_sparepart.employee_id.id
        return res

    sparepart_id = fields.Many2one('sale.order.sparepart', 'Sparepart', readonly=True)
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True)
    qty = fields.Float('Quantity', required=True , default=1)
    attachment = fields.Binary('Salvage Image', required=True)
    attachment_filename = fields.Char('File Name')

    @api.one
    def process_sparepart(self):
        sparepart_id = self.sparepart_id
        sparepart_id.employee_id = self.employee_id.id

        if self.sparepart_id.type == 'order':
            for move in self.sparepart_id.order_line_id.procurement_ids.mapped('move_ids').filtered(lambda r: r.state != 'done' and not r.scrapped):
                # Note that we don't decrease quantity for customer returns on purpose: these are exeptions that must be treated manually. Indeed,
                # modifying automatically the delivered quantity may trigger an automatic reinvoicing (refund) of the SO, which is definitively not wanted
                if move.location_dest_id.usage == "customer":
                    for move_operation in move.linked_move_operation_ids:
                        if move_operation.operation_id.product_qty == move_operation.operation_id.qty_done:
                            raise ValidationError('Already Claim all Product')
                        if move_operation.operation_id.product_qty - move_operation.operation_id.qty_done < self.qty:
                            raise ValidationError('Request was exceeded')
                        move_operation.operation_id.qty_done = self.qty
                        if move_operation.operation_id.product_qty == move_operation.operation_id.qty_done:
                            move.action_done()

        if self.sparepart_id.type == 'insurance':
            move  = self.sparepart_id.production_stock_move_id
            if move.state != 'done':
                move.action_done()
                move.picking_id.action_done()

            #for move_operation in move.linked_move_operation_ids:
            #    if move_operation.operation_id.product_qty == move_operation.operation_id.qty_done:
            #        raise ValidationError('Already Claim all Product')
            #    if move_operation.operation_id.product_qty - move_operation.operation_id.qty_done < self.qty:
            #        raise ValidationError('Request was exceeded')
            #    move_operation.operation_id.qty_done = self.qty
            #    if move_operation.operation_id.product_qty == move_operation.operation_id.qty_done:
            #        move.action_done()

        #Create Salvage Image
        sale_order_id = sparepart_id.sale_order_id
        sale_order_salvage_image_obj = self.env['sale.order.salvage.image']
        sale_order_salvage_image_obj.create({'sale_order_id': sale_order_id.id, 'attachment': self.attachment, 'attachment_filename': self.attachment_filename})


class WizardInsuranceSparepart(models.TransientModel):
    _name = 'wizard.insurance.sparepart'

    @api.model
    def default_get(self, fields):
        res = super(WizardInsuranceSparepart, self).default_get(fields)
        sale_order_sparepart_obj = self.env['sale.order.sparepart']
        active_id = self.env.context.get('active_id') or False
        sale_order_sparepart = sale_order_sparepart_obj.browse(active_id)
        res['sparepart_id'] = sale_order_sparepart.id
        return res

    sparepart_id = fields.Many2one('sale.order.sparepart', 'Sparepart', readonly=True)

    @api.one
    def process_sparepart(self):
        for wizard in self:
            wizard.sparepart_id.stock_move_id.action_assign()
            wizard.sparepart_id.stock_move_id.action_done()


class WizardInsuranceSparepartReceived(models.TransientModel):
    _name = 'wizard.insurance.sparepart.received'

    @api.model
    def default_get(self, fields):
        res = super(WizardInsuranceSparepartReceived, self).default_get(fields)
        sale_order_sparepart_obj = self.env['sale.order.sparepart']
        active_id = self.env.context.get('active_id') or False
        sale_order_sparepart = sale_order_sparepart_obj.browse(active_id)
        res['sparepart_id'] = sale_order_sparepart.id
        return res

    sparepart_id = fields.Many2one('sale.order.sparepart', 'Sparepart', readonly=True)

    @api.one
    def process_sparepart(self):
        for wizard in self:
            wizard.sparepart_id.stock_move_id.action_assign()
            wizard.sparepart_id.stock_move_id.action_done()
            wizard.sparepart_id.stock_move_id.picking_id.do_new_transfer()
            wizard.sparepart_id.production_stock_move_id.picking_id.action_assign()
