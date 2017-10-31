from openerp import models, fields, api


class WizardAddOperator(models.TransientModel):
    _name = 'wizard.add.operator'

    workcenter_line_id = fields.Many2one('mrp.production.workcenter.line', 'Line #', readonly=True)
    operator_id = fields.Many2one('hr.employee','Operator', required=True)
    working_date = fields.Date('Working Date', required=True)

    @api.one
    def add_operator(self):
        active_id = self.env.context.get('active_ids', []) or []
        values = {}
        values.update({'line_id': active_id})
        values.update({'operator': self.operator_id.id})
        values.update({'working_date': self.working_date})
        self.env['mrp.production.workcenter.line.operator'].create(values)


