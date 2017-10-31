import datetime
import pytz
import time
from openerp import tools
from openerp.osv import osv
from openerp.report import report_sxw


class operator_fees(report_sxw.rml_parse):

    def _get_employee_name(self, employee_id):
        employee_obj = self.pool.get('hr.employee')
        return employee_obj.browse(self.cr, self.uid, employee_id)['name']

    def _get_routing_name(self, routing_id):
        mrp_routing_obj = self.pool.get('mrp.routing')
        return mrp_routing_obj.browse(self.cr, self.uid, routing_id)['name']


    def _get_mrp_production_workcenter_line_operators(self, employee_id, periode_fee_id, routing):
        sale_order_obj = self.pool.get('sale.order')
        mrp_production_workcenter_line_operator_obj = self.pool.get('mrp.production.workcenter.line.operator')
        mrp_production_workcenter_line_operator_ids = mrp_production_workcenter_line_operator_obj.search(self.cr, self.uid, [
            ('operator', '=', employee_id),
            ('periode_fee_id', '=', periode_fee_id),
            ('line_id.routing_wc_line', '=', routing[0])]
        )
        mrp_production_workcenter_line_operators = mrp_production_workcenter_line_operator_obj.browse(self.cr, self.uid, mrp_production_workcenter_line_operator_ids)
        return mrp_production_workcenter_line_operators

    def _get_employees(self, form):
        employee_obj = self.pool.get('hr.employee')
        employees = self.pool.get9

    def __init__(self, cr, uid, name, context):
        super(operator_fees, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            '_get_employee_name': self._get_employee_name,
            '_get_mrp_production_workcenter_line_operators': self._get_mrp_production_workcenter_line_operators,
        })


class report_operator_fees(osv.AbstractModel):
    _name = 'report.jakc_sale.report_operatorfees'
    _inherit = 'report.abstract_report'
    _template = 'jakc_sale.report_operatorfees'
    _wrapped_report_class = operator_fees


