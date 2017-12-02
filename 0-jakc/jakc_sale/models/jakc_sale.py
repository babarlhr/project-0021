from datetime import datetime, timedelta
from openerp import SUPERUSER_ID
from openerp import api, fields, models, _, exceptions
import openerp.addons.decimal_precision as dp
from openerp.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
import logging


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = ['sale.order']

    @api.one
    @api.depends('car_status_ids')
    def trans_print_car_status(self):
        print "Car Status"
        total_line = len(self.car_status_ids)
        line = self.car_status_ids(total_line - 1)
        car_status_vals = {}
        car_status_vals.update({'state'})

    @api.one
    @api.depends('production_ids')
    def trans_check_material(self):
        for production in self.production_ids:
            production.action_assign()

        #Calculate Consume Material
        self.trans_merge_stock_move()

    @api.one
    def trans_surat_jalan(self):
        print "Surat Jalan"
        datas = {}
        datas['ids'] = [self.id] or []
        return self.env['report'].get_action(self, 'jakc_sale.report_sale_order_car_status', data=datas)

    @api.multi
    def trans_refresh_workcenter_tree(self):
        pass

    @api.one
    def trans_insurance_sparepart(self):
        stock_picking_obj = self.env['stock.picking']
        company_id = self.env.user.company_id

        vals = {}
        vals.update({'sale_id': self.id})
        vals.update({'partner_id': self.partner_id.id})
        vals.update({'location_id': company_id.location_id.id})
        vals.update({'location_dest_id': company_id.location_dest_id.id})
        vals.update({'move_type': company_id.move_type})
        vals.update({'picking_type_id': company_id.picking_type_id.id})
        vals.update({'priority': company_id.priority})
        result = stock_picking_obj.create(vals)
        result.action_confirm()
        self.sparepart_stock_picking_id = result.id

    def find(self, lst, key, value):
        for i, dic in enumerate(lst):
            if dic[key] == value:
                return i
        return -1

    @api.one
    def trans_merge_stock_move(self):
        consume_material_obj = self.env['sale.order.consume.material']
        consume_material_line_obj = self.env['sale.order.consume.material.line']
        consume_material_ids = self.consume_material_ids

        #for order in self:
        #    order.consume_material_ids.unlink()

        product_lines = []
        product_move_lines = []
        for production_id in self.production_ids:
            for move_line in production_id.move_lines:
                if self.find(product_lines, 'product_id', move_line.product_id.id) == -1:
                    product_line = {}
                    product_line.update({'product_id': move_line.product_id.id})
                    product_line.update({'sale_order_id': self.id})
                    product_lines.append(product_line)

            for move_line2 in production_id.move_lines2:
                if self.find(product_lines, 'product_id', move_line2.product_id.id) == -1:
                    product_line = {}
                    product_line.update({'product_id': move_line2.product_id.id})
                    product_line.update({'sale_order_id': self.id})
                    product_lines.append(product_line)

        for product_line in product_lines:
            #Check Consume Material Product
            args = [('product_id', '=', product_line.product_id)]
            consume_material = consume_material_obj.search(args)
            if consume_material:
                #Update Consume Material
                for production_id in self.production_ids:
                    for move_line in production_id.move_lines:
                        if move_line.product_id.id == res.product_id.id:
                            product_move_line = {}
                            product_move_line.update({'consume_material_id': res.id})
                            product_move_line.update({'stock_move_id': move_line.id})
                            consume_material_line_obj.create(product_move_line)

                    for move_line2 in production_id.move_lines2:
                        if move_line2.product_id.id == res.product_id.id:
                            product_move_line = {}
                            product_move_line.update({'consume_material_id': res.id})
                            product_move_line.update({'stock_move_id': move_line2.id})
                            consume_material_line_obj.create(product_move_line)
            else:
                res = consume_material_obj.create(product_line)
                for production_id in self.production_ids:
                    for move_line in production_id.move_lines:
                        if move_line.product_id.id == res.product_id.id:
                            product_move_line = {}
                            product_move_line.update({'consume_material_id': res.id})
                            product_move_line.update({'stock_move_id': move_line.id})
                            consume_material_line_obj.create(product_move_line)

                    for move_line2 in production_id.move_lines2:
                        if move_line2.product_id.id == res.product_id.id:
                            product_move_line = {}
                            product_move_line.update({'consume_material_id': res.id})
                            product_move_line.update({'stock_move_id': move_line2.id})
                            consume_material_line_obj.create(product_move_line)


    iface_workorder = fields.Boolean('Is Work Order', default=False)
    last_spk = fields.Many2one('sale.order','No SPK Sebelumnya')
    partner_vehicle_id = fields.Many2one('partner.vehicle','Plat Number')
    owner = fields.Many2one('res.partner','Owner', readonly=True)
    printed_num = fields.Integer('Printed #', readonly=True)
    surveyor = fields.Many2one('res.partner','Surveyor')
    driver_in = fields.Many2one('hr.employee','Driver In')
    driver_out = fields.Many2one('hr.employee','Driver Out')
    distance = fields.Selection([
                                ('dekat','Dekat'),
                                ('jauh','Jauh'),
                                ('derek','Derek'),
                                ], 'Distance')

    iface_insurance = fields.Boolean('Is Insurance ?', default=False)
    insurance_company_id = fields.Many2one('res.partner','Insurance')
    insurance_number = fields.Char('Insurance Number', size=50)
    claim_number = fields.Char('Claim Number', size=50)
    claim_date = fields.Date('Claim date')
    or_count = fields.Integer('OR')
    or_amount = fields.Float('OR Fee')
    or_paid_status = fields.Boolean('OR Paid Status', compute="_get_or_paid_status", default=False)
    or_invoice = fields.Many2one('account.invoice', 'Inv #', compute="_get_or_invoice")

    sparepart_stock_picking_id = fields.Many2one('stock.picking','Picking #', readonly=True)
    sparepart_line_ids = fields.One2many('sale.order.sparepart.line','sale_order_id', 'Spareparts')

    estimate_finish_date = fields.Date('Estimate Finish')
    insurance_order_ids = fields.One2many('stock.move', 'sale_order_id', 'Insurance Sparepart')
    attachment_ids = fields.One2many(comodel_name='sale.order.image',  inverse_name='sale_order_id', string='Images')
    before_ids = fields.One2many(comodel_name='sale.order.before.image',  inverse_name='sale_order_id', string='Images')
    after_ids = fields.One2many(comodel_name='sale.order.after.image',  inverse_name='sale_order_id', string='Images')
    production_ids = fields.One2many(comodel_name='mrp.production', inverse_name='sale_order_id', string='Production')
    production_count = fields.Integer(compute="_get_production_count")
    workcenter_line_ids = fields.One2many(comodel_name='mrp.production.workcenter.line', inverse_name='sale_order_id', string='Work Center Line')
    car_status = fields.Many2one(comodel_name='sale.order.car.status',string='Car Status', _compute="get_car_status")
    car_status_str = fields.Text(compute="_get_car_status_str")
    car_type_str = fields.Text(compute="_get_car_status_str")
    car_remark_str = fields.Text(compute="_get_car_status_str")

    car_status_ids = fields.One2many(comodel_name='sale.order.car.status', inverse_name='sale_order_id', string='Cars Status')

    sale_order_percentage = fields.Integer(string='Percentage(%)', compute="_compute_percentage")
    last_workcenter_line = fields.Many2one('mrp.production.workcenter.line', compute="_get_last_workcenter_line")
    operator_workcenter_line = fields.Text(compute="_get_operator_workcenter_line")
    estimate_finish_date_diff = fields.Integer(compute="_get_estimate_finish_date_diff")
    #sparepart_stock_move_ids = fields.One2many(comodel_name='stock.move',string='Spareparts', related='sparepart_stock_picking_id.pick_operation_product_ids')
    sparepart_line_count = fields.Integer(string='Sparepart Count',compute="_get_sparepart_line_count")
    estimate_sparepart_product = fields.Many2one(comodel_name='product.product', compute="_get_estimate_sparepart_product")
    consume_material_ids = fields.One2many('sale.order.consume.material', 'sale_order_id', 'Materials')
    return_material_ids = fields.One2many('sale.order.return.material', 'sale_order_id', 'Materials')
    add_material_ids = fields.One2many('sale.order.add.material', 'sale_order_id', 'Materials')
    scheduled_product_count = fields.Integer(compute="_get_schedule_product_count")
    scheduled_product_amount = fields.Float(string="Material Amount", compute="_get_schedule_product_amount")
    scheduled_product_percentage = fields.Float(string="Material Percentage", compute="_get_schedule_product_amount")

    production_progress = fields.Text(compute="_get_production_status")
    car_actual_in = fields.Datetime(compute="_get_car_actual_in")
    car_actual_out = fields.Datetime(compute="_get_car_actual_out")

    @api.multi
    def action_done(self):
        if self.invoice_status == 'invoiced':
            self.write({'state': 'done'})
        else:
            raise exceptions.Warning(_("Workorder not fully invoiced"))


    @api.one
    @api.depends('invoice_ids')
    def _get_or_paid_status(self):
        paid = False
        for line in self.invoice_ids:
            if line.iface_or_invoice:
                if line.state == 'paid':
                    paid = True
        self.or_paid_status = paid

    @api.one
    @api.depends('invoice_ids')
    def _get_or_invoice(self):
        for line in self.invoice_ids:
            if line.iface_or_invoice:
                self.or_invoice = line

    @api.one
    @api.depends('car_status_ids')
    def _get_car_status_str(self):
        if len(self.car_status_ids) > 0:
            line = self.car_status_ids[0]
            if line.flow_type == 'in':
                self.car_type_str = 'In'
                self.car_status_str = '-'
            else:
                self.car_type_str = 'Out'
                if line.flow_status == '01':
                    self.car_status_str = 'Selesai Perbaikan'
                else:
                    self.car_status_str = 'Rawat Jalan'

            self.car_remark_str = line.remark
        else:
            self.car_status_str = '-'
            self.car_type_str = '-'
            self.car_remark_str = '-'

    @api.one
    @api.depends('car_status_ids')
    def _get_car_status(self):
        if len(self.car_status_ids) > 0:
            line = self.car_status_ids[0]
            self.car_status = line
        else:
            self.car_status = False

    @api.one
    @api.depends('workcenter_line_ids')
    def _compute_percentage(self):
        print "Calculate Percentage"
        finished = 0
        total_line = len(self.workcenter_line_ids)
        for line in self.workcenter_line_ids:
            if line.state == 'done':
                finished += 1
        if total_line == 0:
            self.sale_order_percentage = 0
        else:
            self.sale_order_percentage = int(float(finished) / float(total_line) * 100)

    @api.one
    def _get_estimate_finish_date_diff(self):
        current = datetime.now()
        date_diff = self. estimate_finish_date - current
        self.estimate_finish_date_diff = date_diff

    @api.one
    @api.depends('workcenter_line_ids')
    def _get_last_workcenter_line(self):
        sequence = 0
        company_id = self.env.user.company_id
        routing_wc = company_id.routing_wc
        for production in self.production_ids:
            if production.routing_id.id == routing_wc.id:
                for line in production.workcenter_lines:
                    if line.state in ('done'):
                        if line.sequence > sequence:
                            #self.last_workcenter_line = line.product.name + ' - ' + line.routing_wc_line.name
                            sequence = line.sequence
                            self.last_workcenter_line = line.routing_wc_line.id

    @api.one
    @api.depends('workcenter_line_ids')
    def _get_operator_workcenter_line(self):
        print "Check Operator"
        for line in self.workcenter_line_ids:
            for operator in line.operator01_ids:
                self.operator_workcenter_line = operator.operator.name + "<br/>"
        print self.operator_workcenter_line

    @api.one
    def _get_production_count(self):
        if self.production_ids:
            self.production_count = len(self.production_ids)

    @api.one
    def _get_schedule_product_count(self):
        count = 0
        for production in self.production_ids:
            count += len(production.product_lines)

        self.scheduled_product_count = count

    @api.one
    def _get_schedule_product_amount(self):
        amount = 0.0
        for production in self.production_ids:
            for line in production.move_lines:
                amount += line.product_id.standard_price
        self.scheduled_product_amount = amount
        if self.amount_total:
            self.scheduled_product_percentage = (amount / self.amount_total) * 100
        else:
            self.scheduled_product_percentage = 0.0

    @api.one
    def _get_estimate_sparepart_product(self):
        diff_cmp = 9999;
        for line in self.order_line:
            if line.estimate_sparepart_date:
                diff = datetime.now() - line.estimate_sparepart_date
                if diff < diff_cmp:
                    diff_cmp = diff
                    self.estimate_sparepart_product = line.product_id

    @api.one
    def _get_sparepart_line_count(self):
        count = 0
        for line in self.order_line:
            if not line.product_id.iface_worktype:
                count += 1
        self.sparepart_line_count = count

    @api.one
    def _get_production_status(self):
        total_production = len(self.production_ids)
        total_finish = 0
        for production in self.production_ids:
            if production.state == 'done':
                total_finish += 1
        self.production_progress = str(total_finish) + ' of ' + str(total_production)

    @api.one
    @api.depends('car_status_ids')
    def _get_car_actual_in(self):
        car_status_obj = self.env['sale.order.car.status']
        car_status = car_status_obj.search([('sale_order_id','=', self.id),('flow_type','=','in')], order='trans_date_time desc')
        if car_status:
            self.car_actual_in = car_status[0].trans_date_time
        else:
            self.car_actual_in = ''

    @api.one
    @api.depends('car_status_ids')
    def _get_car_actual_out(self):
        car_status_obj = self.env['sale.order.car.status']
        car_status = car_status_obj.search([('sale_order_id', '=', self.id), ('flow_type', '=', 'out')],
                                           order='trans_date_time desc')
        if car_status:
            self.car_actual_out = car_status[0].trans_date_time
        else:
            self.car_actual_out = ''

    @api.onchange('partner_vehicle_id')
    def change_partner_id(self):
        if self.iface_insurance:
            self.partner_id = self.insurance_company_id
            self.owner = self.partner_vehicle_id.partner_id
        else:
            self.partner_id = self.partner_vehicle_id.partner_id
            self.owner = self.partner_vehicle_id.partner_id

    @api.onchange('insurance_company_id')
    def change_insurance_company_id(self):
        if self.iface_insurance:
            self.partner_id = self.insurance_company_id
            self.or_amount = self.insurance_company_id.or_fee
        else:
            self.partner_id = self.owner

    @api.onchange('iface_insurance')
    def change_iface_insurance(self):
        if self.iface_insurance:
            self.partner_id = self.insurance_company_id
        else:
            self.partner_id = self.owner

    @api.multi
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        # Automatice Reserve Stock for Sale Order
        company_id = self.env.user.company_id
        if company_id.iface_auto_reserve:
            print "Auto Reserve"
            for production in self.production_ids:
                production.action_assign()
        return res

    @api.model
    def create(self ,vals):
        if vals.get('iface_workorder'):
            partner_vehicle = self.env['partner.vehicle'].browse(vals.get('partner_vehicle_id'))
            vals.update({'owner': partner_vehicle.partner_id.id})
            if vals.get('iface_insurance'):
                vals.update({'partner_id': vals.get('insurance_company_id')})
            else:
                vals.update({'partner_id': partner_vehicle.partner_id.id})
            result = super(SaleOrder, self).create(vals)

            #Generate Consume Summarize
            #Create First Car Status
            #car_status_vals = {}
            #car_status_vals.update({'sale_order_id': result.id})
            #car_status_vals.update({'trans_date_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
            #car_status_vals.update({'flow_type': 'in'})
            #self.env['sale.order.car.status'].create(car_status_vals)

            return result

        return super(SaleOrder, self).create(vals)



    @api.multi
    def print_quotation(self):
        res = super(SaleOrder,self).print_quotation()
        printed_num = self.printed_num + 1
        self.write({'printed_num': printed_num})
        return res

    @api.multi
    def open_url_detail(self):
        return {
            "type": "ir.actions.act_url",
            "url": "/workshop/workorder/detail/" + self.name,
            "target": "new",
        }

    @api.multi
    def process_or(self):
        company_id = self.env.user.company_id
        or_product = company_id.or_product

        val = {
            'name': or_product.name,
            'product_uom_qty': self.or_count,
            'order_id': self.id,
            'product_id': or_product.id or False,
            'product_uom': or_product.uom_id.id,
        }
        self.env['sale.order.line'].create(val)
        return True


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.multi
    def _prepare_invoice_line(self, qty):

        """
        Prepare the dict of values to create the new invoice line for a sales order line.

        :param qty: float quantity to invoice
        """
        self.ensure_one()
        res = {}
        account = self.product_id.property_account_income_id or self.product_id.categ_id.property_account_income_categ_id
        if not account:
            raise exceptions.ValidationError(
                _('Please define income account for this product: "%s" (id:%d) - or for its category: "%s".') % \
                (self.product_id.name, self.product_id.id, self.product_id.categ_id.name))

        fpos = self.order_id.fiscal_position_id or self.order_id.partner_id.property_account_position_id
        if fpos:
            account = fpos.map_account(account)

        res = {
            'name': self.name,
            'sequence': self.sequence,
            'origin': self.order_id.name,
            'sale_order_id': self.order_id.id,
            'account_id': account.id,
            'price_unit': self.price_unit,
            'quantity': qty,
            'discount': self.discount,
            'uom_id': self.product_uom.id,
            'product_id': self.product_id.id or False,
            'invoice_line_tax_ids': [(6, 0, self.tax_id.ids)],
            'account_analytic_id': self.order_id.project_id.id,
        }
        return res

    estimate_sparepart_date = fields.Date('Estimate Date')


    @api.multi
    def write(self, vals):
        if 'product_uom_qty' in vals.keys():
            if vals.get('product_uom_qty') <= 0:
                mrp_production_obj = self.env['mrp.production']
                args = [('sale_line_id','=', self.id)]
                mrp_production_ids = mrp_production_obj.search(args)
                for mrp_production_id in mrp_production_ids:
                    mrp_production_id.action_cancel()
                    logger.info("Execute Cancel Production")

        return super(SaleOrderLine, self).write(vals)



class SaleOrderSparepartLine(models.Model):
    _name = 'sale.order.sparepart.line'

    @api.multi
    def _make_stock_move(self):
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
            #vals.update({'company_id': line.})
            vals.update({'procure_method': 'make_to_stock'})
            vals.update({'origin': line.sale_order_id.name})
            stock_move = stock_move_obj.create(vals)
            stock_move.action_confirm()
            line.stock_move_id = stock_move.id
        return stock_move

    sale_order_id = fields.Many2one('sale.order', 'Order #', readonly=True)
    product_id = fields.Many2one('product.product', 'Product', required=True)
    product_uom_qty = fields.Float('Quantity', required=True)
    product_uom = fields.Many2one('product.uom', 'Unit of Measure', required=True)
    expected_date = fields.Date('Expected Date', required=True)
    stock_move_id = fields.Many2one('stock.m    ove','Stock Move', readonly=True)

    @api.model
    def create(self, vals):
        sparepart_line = super(SaleOrderSparepartLine, self).create(vals)
        stock_move = sparepart_line._make_stock_move()
        return sparepart_line

class SaleOrderImages(models.Model):
    _name = 'sale.order.image'

    sale_order_id = fields.Many2one('sale.order','Sale Order')
    attachment = fields.Binary('Image')
    attachment_filename = fields.Char('File Name')

class SaleOrderBeforemages(models.Model):
    _name = 'sale.order.before.image'

    sale_order_id = fields.Many2one('sale.order','Sale Order')
    attachment = fields.Binary('Image')
    attachment_filename = fields.Char('File Name')

class SaleOrderAfterImages(models.Model):
    _name = 'sale.order.after.image'

    sale_order_id = fields.Many2one('sale.order','Sale Order')
    attachment = fields.Binary('Image')
    attachment_filename = fields.Char('File Name')


class SaleOrderRouting(models.Model):
    _name = 'sale.order.routing'

    @api.one
    @api.depends('production_ids')
    def _compute_percentage(self):
        finished = 0
        total_line = len(self.production_ids)
        for line in self.production_ids:
            if line.state == 'done':
                finished += 1
        self.routing_wc_line_percentage = int((float(finished) / float(total_line)) * 100)

    sale_order_id = fields.Many2one('sale.order','Sale Order')
    routing_wc = fields.Many2one('mrp.routing', 'Routing')
    routing_wc_percentage = fields.Integer('Percentage', _compute="_compute_percentage")


class SaleOrderCarStatus(models.Model):
    _name = 'sale.order.car.status'
    _order = 'trans_date_time desc'

    @api.multi
    def get_last_status(self, sale_order_id):
        cars = self.browse([('sale_order_id','=',sale_order_id)], order='trans_date_time desc')
        if cars:
            return cars[0]
        else:
            return False

    sale_order_id = fields.Many2one('sale.order','Sale Order')
    trans_date_time = fields.Datetime('Date and Time', required=True)
    flow_type = fields.Selection([('in','In'),('out','Out')], 'Type', readonly=False, required=True)
    flow_status = fields.Selection([('01','Selesai Perbaikan'),('02','Rawat Jalan')],'Status')
    print_number = fields.Integer('Print #', readonly=True)
    remark = fields.Char('Remark', size=200)
    state = fields.Selection([('open','Open'),('done','Done')], 'Status', readonly=False, default='open')


class SaleOrderConsumeMaterial(models.Model):
    _name = 'sale.order.consume.material'

    @api.one
    def _calculate_product_uom_qty(self):
        sale_order_add_material_obj = self.env['sale.order.add.material']
        sale_order_return_material_obj = self.env['sale.order.return.material']
        qty = 0
        for consume_material in self:
            for material in consume_material:
                for line in material.line_ids:
                    qty += line.stock_move_id.product_uom_qty

                args = [('sale_order_id', '=', consume_material.sale_order_id.id),('product_id', '=', consume_material.product_id.id)]
                # Calculate Add Quantity
                add_material_ids = sale_order_add_material_obj.search(args)
                for add_material in add_material_ids:
                    qty += add_material.product_uom_qty
                # Calculate Return Quantity
                return_material_ids = sale_order_return_material_obj.search(args)
                for return_material in return_material_ids:
                    qty -= return_material.product_uom_qty

                self.quantity = qty
                qty = 0

    @api.one
    def _calculate_product_quant_qty(self):
        qty_done = 0
        for consume_material in self:
            for material in consume_material:
                for line in material.line_ids:
                    for quant in line.stock_move_id.quant_ids:
                        qty_done += quant.qty
                self.quantity_done = qty_done
                qty_done = 0

    @api.one
    def _calculate_quantity_add(self):
        sale_order_add_material_obj = self.env['sale.order.add.material']
        sale_order_return_material_obj = self.env['sale.order.return.material']
        qty = 0
        for consume_material in self:
            args = [('sale_order_id','=', consume_material.sale_order_id.id),('product_id', '=', consume_material.product_id.id)]
            # Calculate Add Quantity
            add_material_ids = sale_order_add_material_obj.search(args)
            for add_material in add_material_ids:
                qty += add_material.product_uom_qty
            # Calculate Return Quantity
            self.quantity_add = qty
            qty = 0


    @api.one
    def _calculate_quantity_return(self):
        sale_order_add_material_obj = self.env['sale.order.add.material']
        sale_order_return_material_obj = self.env['sale.order.return.material']
        qty = 0
        for consume_material in self:
            args = [('sale_order_id','=', consume_material.sale_order_id.id),('product_id', '=', consume_material.product_id.id)]
            # Calculate Add Quantity
            return_material_ids = sale_order_return_material_obj.search(args)
            for return_material in return_material_ids:
                qty += return_material.product_uom_qty
            # Calculate Return Quantity
            self.quantity_return = qty
            qty = 0


    @api.one
    def trans_consume_material(self):
        #Consume Default Material
        for material in self:
            for line in material.line_ids:
                move = line.stock_move_id
                if move.state == 'assigned':
                    move_obj = self.env['stock.move']
                    uom_obj = self.env['product.uom']
                    production_obj = self.env['mrp.production']
                    production_id = move.raw_material_production_id.id
                    production = production_obj.browse(production_id)
                    if production.state in ['ready','in_production']:
                        logger.info("Production ID : " + str(production.id))
                        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
                        qty = uom_obj._compute_qty(move.product_uom.id, move.product_uom_qty, move.product_id.uom_id.id)
                        logger.info("QTY : "  + str(qty))
                        remaining_qty = move.product_uom_qty - qty
                        logger.info("Remaining QTY : " + str(remaining_qty))
                        # check for product quantity is less than previously planned
                        if float_compare(remaining_qty, 0, precision_digits=precision) >= 0:
                            logger.info('Move ID')
                            logger.info(move.id)
                            #res = move_obj.action_consume([move.id], qty, move.location_id.id)
                            res = move.action_consume(qty, move.location_id.id)
                        else:
                            consumed_qty = min(move.product_uom_qty, qty)
                            new_moves = move.action_consume(consumed_qty, move.location_id.id)
                            # consumed more in wizard than previously planned
                            extra_more_qty = qty - consumed_qty
                            # create new line for a remaining qty of the product
                            extra_move_id = production_obj._make_consume_line_from_data(production,
                                                                                        move.product_id.id,
                                                                                        move.product_id.uom_id.id,
                                                                                        extra_more_qty)
                            #move_obj.write([extra_move_id], {'restrict_lot_id': data.restrict_lot_id.id},context=context)
                            move_obj.action_done([extra_move_id])
                            logger.info("Move 02")

        #Consume Additional Material

    sale_order_id = fields.Many2one('sale.order','Order #')
    employee_id = fields.Many2one('hr.employee','Employee', readonly=True)
    product_id = fields.Many2one('product.product', 'Product')
    quantity = fields.Float(compute='_calculate_product_uom_qty', string='Quantity')
    quantity_done = fields.Float(compute='_calculate_product_quant_qty', string='Claimed')
    quantity_add = fields.Float(compute='_calculate_quantity_add', string='Add')
    quantity_return = fields.Float(compute='_calculate_quantity_return', string='Return')
    line_ids = fields.One2many('sale.order.consume.material.line', 'consume_material_id', 'Material Lines')


class SaleOrderConsumeMaterialLine(models.Model):
    _name = 'sale.order.consume.material.line'

    consume_material_id = fields.Many2one('sale.order.consume.material','Consume Material #')
    stock_move_id = fields.Many2one('stock.move','Move #')


class SaleOrderAddMaterial(models.Model):
    _name ='sale.order.add.material'

    sale_order_id = fields.Many2one('sale.order','Order #')
    employee_id = fields.Many2one('hr.employee','Employee', readonly=True)
    trans_date = fields.Date('Date', required=True, select=True, default=lambda self: fields.datetime.now())
    product_id = fields.Many2one('product.product', 'Product')
    product_uom_qty = fields.Float('Quantity', related='stock_move_id.product_uom_qty', store=True,)
    product_uom = fields.Many2one('product.uom', 'Unit of Measure', required=True)
    stock_move_id = fields.Many2one('stock.move', 'Move', readonly=True)
    iface_approval = fields.Boolean('Need Approval', default=False, readonly=True)
    approved_by = fields.Many2one('hr.employee', 'Approved By', readonly=True)

class SaleOrderAddMaterialLine(models.Model):
    _name = 'sale.order.add.material.line'

    add_material_id = fields.Many2one('sale.order.add.material','Add Material #')
    stock_move_id = fields.Many2one('stock.move','Move #')


class SaleOrderReturnMaterial(models.Model):
    _name = 'sale.order.return.material'

    sale_order_id = fields.Many2one('sale.order', 'Order #')
    employee_id = fields.Many2one('hr.employee','Employee', readonly=True)
    trans_date = fields.Date('Date', required=True, select=True, default=lambda self: fields.datetime.now())
    product_id = fields.Many2one('product.product', 'Product', required=True)
    product_uom_qty = fields.Float('Quantity', related='stock_move_id.product_uom_qty', store=True,)
    product_uom = fields.Many2one('product.uom', 'Unit of Measure', required=True)
    stock_move_id = fields.Many2one('stock.move', 'Move', readonly=True)


class SaleOrderReturnMaterialLine(models.Model):
    _name = 'sale.order.return.material.line'

    return_material_id = fields.Many2one('sale.order.consume.material','Consume Material #')
    stock_move_id = fields.Many2one('stock.move','Move #')


class JakcWorkshop(models.Model):
    _inherit = ['partner.vehicle']

    workorder_ids = fields.One2many('sale.order', 'partner_vehicle_id', 'Workorders')




