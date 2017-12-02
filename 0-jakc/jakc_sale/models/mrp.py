from datetime import datetime, timedelta
from openerp import SUPERUSER_ID
from openerp import api, fields, models, _ , exceptions
import openerp.addons.decimal_precision as dp
from openerp.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
import logging


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    @api.one
    def _calculate_bom_cost(self):
        total = 0
        for line in self.bom_line_ids:
            total += (line.standard_price * line.product_qty)
        self.bom_cost = total

    @api.one
    @api.depends('bom_line_ids')
    def _get_total_material_cost(self):
        total = 0
        for bom_line in self.bom_line_ids:
            total += bom_line.product_id.standart_price
        self.total_material_cost = total

    bom_cost = fields.Float(string='Bom Cost', compute='_calculate_bom_cost')
    list_price = fields.Float(string='Price', related='product_tmpl_id.list_price')
    total_material_cost = fields.Float(string='Total Material Cost', compute='_get_total_material_cost')


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    standard_price = fields.Float(string='Cost Price', related='product_id.standard_price')


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

class MrpRoutingWorkCenter(models.Model):
    _inherit = ['mrp.routing.workcenter']

    @api.one
    def _compute_workcenter_count(self):
        workcenter_line_obj = self.env['mrp.production.workcenter.line']
        args = [('routing_wc_line','=', self.id)]
        workcenter_line_ids = workcenter_line_obj.search(args)
        if workcenter_line_ids:
            self.workcenter_count = len(workcenter_line_ids)

    @api.one
    def _compute_workcenter_draft(self):
        workcenter_line_obj = self.env['mrp.production.workcenter.line']
        args = [('routing_wc_line', '=', self.id),('state','=', 'draft')]
        workcenter_line_ids = workcenter_line_obj.search(args)
        if workcenter_line_ids:
            self.workcenter_draft = len(workcenter_line_ids)

    @api.one
    def _compute_workcenter_startworking(self):
        workcenter_line_obj = self.env['mrp.production.workcenter.line']
        args = [('routing_wc_line', '=', self.id), ('state', '=', 'startworking')]
        workcenter_line_ids = workcenter_line_obj.search(args)
        if workcenter_line_ids:
            self.workcenter_startworking = len(workcenter_line_ids)

    mechanic_percentage = fields.Float('Mechanic Percentage', required=True)
    workcenter_count = fields.Integer(string='Workcenter Count', compute="_compute_workcenter_count")
    workcenter_draft = fields.Integer(string='Workcenter Draft', compute="_compute_workcenter_draft")
    workcenter_startworking = fields.Integer(string='Workcenter In progress', compute="_compute_workcenter_startworking")

class MrpProductionWorkcenterLine(models.Model):
    _inherit = ['mrp.production.workcenter.line']

    @api.one
    def trans_start_working(self):
        routing_wc_line = self.routing_wc_line.id
        production_workcenter_line_obj= self.env['mrp.production.workcenter.line']
        args = [('sale_order_id', '=', self.sale_order_id.id),('routing_wc_line', '=', self.routing_wc_line.id)]
        workcenter_line_ids = production_workcenter_line_obj.search(args)
        for line in workcenter_line_ids:
            line.action_start_working()

    @api.one
    def _get_operators(self):
        print "Get Operators"
        self.list_operator = ''
        operator01_ids = self.operator01_ids
        for operator in operator01_ids:
            self.list_operator = self.list_operator + operator.operator.name + ', '

    @api.one
    def trans_request_approve(self):
        self.action_done()

    @api.one
    def trans_request_reject(self):
        self.action_start_working()

    @api.one
    def trans_request_qc(self):
        self.action_request_qc()

    @api.one
    def action_request_qc(self):
        logger.info("Start Action Request QC")
        if len(self.operator01_ids) > 0:
            logger.info("Action Request QC")
            self.write({'state': 'request'})
        else:
            raise exceptions.Warning(_("Please define Operators!"))

    @api.one
    def action_start_working(self):
        production_ids  = self.sale_order_id.production_ids
        for production in production_ids:
            for line in production.workcenter_lines:
                if line.routing_wc_line.id == self.routing_wc_line.id:
                    result = super(MrpProductionWorkcenterLine, line).action_start_working()
        return True

    #@api.one
    #def action_start_working(self):
    #    for move in self.move_lines:
    #        if move.state != 'done':
    #            raise exceptions.Warning(_("Please consume product before production"))
    #    return super(MrpProductionWorkcenterLine, self).action_start_working()

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

    attachment_ids = fields.One2many('mrp.production.workcenter.line.image', 'line_id', 'Images')
    operator01_ids = fields.One2many('mrp.production.workcenter.line.operator', 'line_id', 'Operators')
    list_operator = fields.Text(string='Operators', compute="_get_operators")

    state = fields.Selection(
        [('draft', 'Draft'), ('cancel', 'Cancelled'), ('pause', 'Pending'), ('startworking', 'In Progress'), ('request','Request'),
         ('done', 'Finished')], 'Status', readonly=True, copy=False,
        help="* When a work order is created it is set in 'Draft' status.\n" \
             "* When user sets work order in start mode that time it will be set in 'In Progress' status.\n" \
             "* When work order is in running mode, during that time if user wants to stop or to make changes in order then can set in 'Pending' status.\n" \
             "* When the user cancels the work order it will be set in 'Canceled' status.\n" \
             "* When order is completely processed that time it is set in 'Finished' status.")

class MrpProductionWorkcenterLineImage(models.Model):
    _name = 'mrp.production.workcenter.line.image'

    line_id = fields.Many2one('mrp.production.workcenter.line', 'Work Center #')
    attachment = fields.Binary('Image')
    state = fields.Selection([('before', 'Before'), ('after', 'After')], 'State')

class MrpProductionWorkcenterLineOperator(models.Model):
    _name = 'mrp.production.workcenter.line.operator'

    @api.one
    def _calculate_fee(self):
        line_id  = self.line_id
        if line_id.state == 'done':
            self.operator_fee = line_id.product.list_price * 0.25 * (line_id.routing_wc_line.mechanic_percentage / 100)

    line_id = fields.Many2one('mrp.production.workcenter.line', 'Work Center #')
    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        related='line_id.sale_order_id',
        readonly=True,
        store=True,
        string='Workorder #')
    operator = fields.Many2one('hr.employee', 'Operator', required=True)
    workingdate = fields.Date('Working Date', required=True)
    operator_fee = fields.Float(string='Fee', compute="_calculate_fee")
    periode_fee_id = fields.Many2one('hr.employee.periode.fee','Periode')
    fee_amount = fields.Float(string='Amount')
    paid_state = fields.Selection([('notpaid', 'Not Paid'),('paid', 'Paid')], 'Paid Status', default='notpaid')
    state = fields.Selection([('open','Open'),('done','Close')], 'Status', default='open')

class MrpProductionProductLine(models.Model):
    _inherit = 'mrp.production.product.line'

    iface_additional = fields.Boolean('Additional', default=False)

