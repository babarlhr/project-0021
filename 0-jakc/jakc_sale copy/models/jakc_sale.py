from datetime import datetime, timedelta
from openerp import SUPERUSER_ID
from openerp import api, fields, models, _
import openerp.addons.decimal_precision as dp
from openerp.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
import logging


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = ['sale.order']

    iface_workorder = fields.Boolean('Is Work Order', default=False)
    last_spk = fields.Many2one('sale.order','No SPK Sebelumnya')
    partner_vehicle_id = fields.Many2one('partner.vehicle','Plat Number')
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
    or_amount = fields.Float('Amount Per OR')

    estimate_finish_date = fields.Date('Estimate Finish')
    attachment_ids = fields.One2many(comodel_name='sale.order.image',  inverse_name='sale_order_id', string='Images')
    production_ids = fields.One2many(comodel_name='mrp.production', inverse_name='sale_order_id', string='Production')
    production_count = fields.Integer(compute="_get_production_count")
    workcenter_line_ids = fields.One2many(comodel_name='mrp.production.workcenter.line', inverse_name='sale_order_id', string='Work Center Line')
    sale_order_percentage = fields.Integer(string='Percentage(%)', compute="_compute_percentage")

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
    def _get_production_count(self):
        if self.production_ids:
            self.production_count = len(self.production_ids)

    @api.onchange('partner_vehicle_id')
    def change_partner_id(self):
        self.partner_id = self.partner_vehicle_id.partner_id

    @api.model
    def create(self ,vals):
        if vals.get('iface_workorder'):
            partner_vehicle = self.env['partner.vehicle'].browse(vals.get('partner_vehicle_id'))
            vals.update({'partner_id': partner_vehicle.partner_id.id})
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


class SaleOrderImages(models.Model):
    _name = 'sale.order.image'

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

    sale_order_id = fields.Many2one('sale.order','Sale Order')
    trans_date_time = fields.Datetime('Date and Time', required=True)
    flow_state = fields.Selection([('in','In'),('out','Out')], 'Type', required=True)

class JakcWorkshop(models.Model):
    _inherit = ['partner.vehicle']

    workorder_ids = fields.One2many('sale.order', 'partner_vehicle_id', 'Workorders')


class ProcurementOrder(models.Model):
    _inherit = ['procurement.order']

    sale_order_id = fields.Many2one('sale.order','Sale Order',readonly=True)
    partner_vehicle_id = fields.Many2one('partner.vehicle', related='sale_order_id.partner_vehicle_id', readonly=True, string='Vehicle')


class MrpProduction(models.Model):
    _inherit = ['mrp.production']

    @api.one
    @api.depends('workcenter_lines')
    def _compute_percentage(self):
        finished = 0
        total_line = len(self.workcenter_lines)
        for line in self.workcenter_lines:
            if line.state == 'done':
                finished += 1
        if total_line == 0:
            self.routing_wc_line_percentage = 0
        else:
            self.routing_wc_line_percentage = int((float(finished) / float(total_line)) * 100)

    partner_id = fields.Many2one(
        comodel_name='res.partner', string='Customer', store=True,
        related='move_prod_id.procurement_id.sale_line_id.order_id.partner_id')

    sale_order_id = fields.Many2one(
        comodel_name='sale.order', string='Sale Order', store=True,
        related='move_prod_id.procurement_id.sale_line_id.order_id')

    partner_vehicle_id = fields.Many2one('partner.vehicle', related='sale_order_id.partner_vehicle_id', readonly=True, string='Vehicle')

    sale_line_id = fields.Many2one(
        comodel_name='sale.order.line', string='Sale Line', store=True,
        related='move_prod_id.procurement_id.sale_line_id')

    routing_wc_line_percentage = fields.Integer(string='Percentage(%)', compute="_compute_percentage")


class MrpProductionWorkcenterLine(models.Model):
    _inherit = ['mrp.production.workcenter.line']


    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        related='production_id.sale_order_id',
        readonly=True,
        store=True,
        string='Workorder #')

    partner_vehicle_id = fields.Many2one(
        comodel_name='partner.vehicle',
        related='sale_order_id.partner_vehicle_id',
        readonly=True,
        string='Vehicle')

    attachment_ids = fields.One2many('mrp.production.workcenter.line.image','line_id','Images')
    operator_ids = fields.One2many('mrp.production.workcenter.line.operator','line_id','Operators')


class MrpProductionWorkcenterLineImage(models.Model):
    _name = 'mrp.production.workcenter.line.image'

    line_id = fields.Many2one('mrp.production.workcenter.line', 'Work Center #')
    attachment = fields.Binary('Image')
    state = fields.Selection([('before','Before'),('after','After')],'State')


class MrpProductionWorkcenterLineOperator(models.Model):
    _name = 'mrp.production.workcenter.line.operator'

    line_id = fields.Many2one('mrp.production.workcenter.line', 'Work Center #')
    operator = fields.Many2one('hr.employee', 'Operator', required=True)
    workingdate = fields.Date('Working Date', required=True)


