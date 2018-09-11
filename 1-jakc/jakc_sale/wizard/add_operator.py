from openerp import models, fields, api
from datetime import datetime

class WizardAddOperator(models.TransientModel):
    _name = 'wizard.add.operator'

    operator_id = fields.Many2one('hr.employee','Operator', required=False)
    iface_operator_fee = fields.Boolean('Operator Fee', default=True)
    working_date = fields.Date('Working Date', required=True)

    @api.one
    def add_operator(self):
        active_id = self.env.context.get('active_id') or False
        values = {}
        values.update({'line_id': active_id})
        values.update({'operator': self.operator_id.id})
        values.update({'iface_operator_fee': self.iface_operator_fee})
        values.update({'workingdate': self.working_date})
        self.env['mrp.production.workcenter.line.operator'].create(values)


class WizardAddOperatorMain(models.TransientModel):
    _name = 'wizard.add.operator.main'

    @api.model
    def default_get(self, fields):
        res = super(WizardAddOperatorMain, self).default_get(fields)
        active_id = self.env.context.get('active_id') or False
        workcenter_line = self.env['mrp.production.workcenter.line'].browse(active_id)
        if 'routing_id' in fields:
            res.update({'routing_id': workcenter_line.routing_wc_line.routing_id.id})
        if 'workcenter_id' in fields:
            res.update({'workcenter_id': workcenter_line.routing_wc_line.id})
        return res

    def _check_operator(self, operator_ids, operator_id):
        exist = False
        for operator in operator_ids:
            if operator.id == operator_id:
                exist = True
                break
        return exist

    @api.one
    def add_operator(self):
        active_id = self.env.context.get('active_id') or False
        workcenter_line = self.env['mrp.production.workcenter.line'].browse(active_id)
        args = [('sale_order_id','=', workcenter_line.sale_order_id.id), ('routing_wc_line','=', self.workcenter_id.id)]
        production_workcenter_line_ids = self.env['mrp.production.workcenter.line'].search(args)
        for line in production_workcenter_line_ids:
            if not self._check_operator(line.operator01_ids, self.operator_id.id):
                values = {}
                values.update({'line_id': line.id})
                values.update({'operator': self.operator_id.id})
                values.update({'workingdate': self.working_date})
                self.env['mrp.production.workcenter.line.operator'].create(values)

    routing_id = fields.Many2one('mrp.routing','Routing', readonly=True, required=False)
    workcenter_id = fields.Many2one('mrp.routing.workcenter', 'Workcenter', readonly=True, required=False)
    iface_operator_fee = fields.Boolean('Operator Fee', default=True)
    operator_id = fields.Many2one('hr.employee','Operator', required=False)
    working_date = fields.Date('Working Date', required=True, default=datetime.now())

