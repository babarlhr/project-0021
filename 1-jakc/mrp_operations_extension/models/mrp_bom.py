# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError
import math


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    @api.one
    def trans_routing_price(self):
        mrp_bom_routing_price_obj = self.env['mrp.bom.routing.price']
        for bom in self:
            if bom.routing_id:
                for workcenter_line in bom.routing_id.workcenter_lines:
                    args = [('bom_id','=', bom.id),('workcenter_id','=', workcenter_line.id)]
                    mrp_bom_routing_price = mrp_bom_routing_price_obj.search(args)
                    if not mrp_bom_routing_price:
                        values = {}
                        values.update({'bom_id':bom.id})
                        values.update({'workcenter_id': workcenter_line.id})
                        values.update({'fee_type': '01'})
                        values.update({'mechanic_percentage': 0.0})
                        values.update({'mechanic_fix': 0.0})
                        result = mrp_bom_routing_price_obj.create(values)
            else:
                raise ValidationError('Please define routing for this BOM!')

    @api.multi
    def _prepare_wc_line(self, wc_use, level=0, factor=1):
        res = super(MrpBom, self)._prepare_wc_line(
            wc_use, level=level, factor=factor)
        cycle = int(math.ceil(factor / (wc_use.cycle_nbr or 1)))
        hour = wc_use.hour_nbr * cycle
        default_wc_line = wc_use.op_wc_lines.filtered(lambda r: r.default)
        if default_wc_line.custom_data:
            time_start = default_wc_line.time_start
            time_stop = default_wc_line.time_stop
        else:
            time_start = default_wc_line.workcenter.time_start
            time_stop = default_wc_line.workcenter.time_stop
        res.update({
            'cycle': cycle,
            'hour': hour,
            'time_start': time_start,
            'time_stop': time_stop,
            'routing_wc_line': wc_use.id,
            'do_production': wc_use.do_production,
        })
        return res

    @api.model
    def _prepare_consume_line(self, bom_line, quantity, factor=1):
        res = super(MrpBom, self)._prepare_consume_line(
            bom_line, quantity, factor=factor)
        res['bom_line'] = bom_line.id
        return res

    @api.multi
    @api.onchange('routing_id')
    def onchange_routing_id(self):
        for line in self.bom_line_ids:
            line.operation = self.routing_id.workcenter_lines[:1]
        if self.routing_id:
            return {'warning': {
                    'title': _('Changing Routing'),
                    'message': _("Changing routing will cause to change the"
                                 " operation in which each component will be"
                                 " consumed, by default it is set the first"
                                 " one of the routing")
                    }}
        return {}

    routing_price_ids = fields.One2many('mrp.bom.routing.price','bom_id','Routing Prices')


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    @api.model
    def _get_default_operation(self):
        routing_id = self.routing_id.id
        args = [('routing_id','=', routing_id),('do_material','=', True)]
        mrp_routing_worcenter_ids = self.env['mrp.routing.workcenter'].search(args)
        if mrp_routing_worcenter_ids:
            return mrp_routing_worcenter_ids[0].id
        return False

    operation = fields.Many2one(comodel_name='mrp.routing.workcenter', string='Consumed in', default=_get_default_operation)


class MrpBomRoutingPrice(models.Model):
    _name = 'mrp.bom.routing.price'

    bom_id = fields.Many2one('mrp.bom','Bom #', index=True)
    workcenter_id = fields.Many2one(comodel_name='mrp.routing.workcenter', string='Workcenter', required=True)
    fee_type = fields.Selection([('01','Percentage'),('02','Fixed')],'Fee Type', default='01', required=True)
    mechanic_percentage = fields.Float('Mechanic Percentage', required=True, default=0)
    mechanic_fix = fields.Float('Mechanic Fix', required=True, default=0)



