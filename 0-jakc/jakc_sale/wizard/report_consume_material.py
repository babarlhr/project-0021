import time
from openerp.osv import osv, fields


class ConsumeMaterials(osv.osv_memory):
    _name = 'consume.materials'
    _description = 'Consume Materials'

    _columns = {
        'date_start': fields.date('Start Date', required=True),
        'date_end': fields.date('End Date', required=True),
    }

    def print_report(self, cr, uid, ids, context=None):
        print "Print Consume Materials"
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        res = self.read(cr, uid, ids, ['date_start', 'date_end'], context=context)
        res = res and res[0] or {}
        datas['form'] = res
        if res.get('id', False):
            datas['ids'] = [res['id']]

        return self.pool['report'].get_action(cr, uid, [], 'jakc_sale.report_consumematerials', data=datas, context=context)