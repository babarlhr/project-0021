from openerp import api, fields, models, _

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    workcenter_line_ids = fields.One2many('mrp.production.workcenter.line.operator', 'operator', 'Workcenters')


class HrEmployeePeriodeFee(models.Model):
    _name = 'hr.employee.periode.fee'

    @api.one
    def process_operator_fee(self):
        production_workcenter_line_operator_obj = self.env['mrp.production.workcenter.line.operator']
        args = [('workingdate', '>=', self.date_start),
                ('workingdate', '<', self.date_end),
                ('line_id.state','=','done'),
                ('state','=','open'),]
        wc_line_operator_ids = production_workcenter_line_operator_obj.search(args)
        for wc_line_operator in wc_line_operator_ids:
            print wc_line_operator.operator.name
            fee_amount = wc_line_operator.line_id.product.list_price * 0.25 * (wc_line_operator.line_id.routing_wc_line.mechanic_percentage / 100)
            vals = {}
            vals.update({'periode_fee_id': self.id})
            vals.update({'fee_amount': fee_amount})
            vals.update({'state': 'done'})
            wc_line_operator.write(vals)

    name = fields.Char('Name', readonly=True)
    date_start = fields.Date("Start Date", required=True)
    date_end = fields.Date("End Date", required=True)
    number_of_employee = fields.Date("Number of Employee", readonly=True)
    total_amount = fields.Float("Total Amount", readonly=True)
    state = fields.Selection([('open', 'Open'), ('done', 'Close')], 'Status', readonly=True)
    workcenter_line_ids = fields.One2many('mrp.production.workcenter.line.operator', 'periode_fee_id', 'Workcenters')


    @api.model
    def create(self, vals):
        vals.update({'name': vals.get('date_start') + ' - ' + vals.get('date_end')})
        return super(HrEmployeePeriodeFee, self).create(vals)


