import time
from openerp.osv import osv, fields


class OperatorFees(osv.osv_memory):
    _name = 'operator.fees'
    _description = 'Operator Fees'

    def onchange_routing(self, cr, uid, ids, routing, context=None):
        res = {}
        mrp_routing_workcenter_obj = self.pool.get('mrp.routing.workcenter')
        routing_workcenter_ids = mrp_routing_workcenter_obj.search(cr, uid, [('routing_id', '=', routing)])
        return {'domain': {'routing_wc': [('id', 'in', routing_workcenter_ids)]}}

    _columns = {
        'periode_fee': fields.many2one('hr.employee.periode.fee','Periode Fee', required=True),
        'routing': fields.many2one('mrp.routing', 'Routing', required=True),
        'routing_wc': fields.many2one('mrp.routing.workcenter', 'Routing Workcenter', required=True),
        'employee_ids': fields.many2many('hr.employee', 'operator_fees_report_employee_rel', 'employee_id', 'wizard_id', 'Employees'),
    }

    def print_report(self, cr, uid, ids, context=None):
        print "Print Operator Fees"
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        res = self.read(cr, uid, ids, ['periode_fee', 'routing', 'routing_wc', 'employee_ids'], context=context)
        res = res and res[0] or {}
        datas['form'] = res
        if res.get('id', False):
            datas['ids'] = [res['id']]

        return self.pool['report'].get_action(cr, uid, [], 'jakc_sale.report_operatorfees', data=datas, context=context)