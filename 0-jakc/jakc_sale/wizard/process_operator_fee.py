import time
from openerp.osv import osv, fields


class ProcessOperatorFee(osv.osv_memory):
    _name = 'process.operator.fee'
    _description = 'Process Operator Fee'

    _columns = {
        'periode': fields.date('Periode', domain=[('state','=','open')], required=True)
    }

    def process_operator_fee(self, cr, uid, ids, context=None):
        print "Process Operator Fee"
        hr_employee_periode_fee_obj = self.pool.get('hr.employee.periode.fee')
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        res = self.read(cr, uid, ids, ['periode'], context=context)
        hr_employee_periode_fee_obj.process_operator_fee(cr, uid, res['periode'][0], context=context)