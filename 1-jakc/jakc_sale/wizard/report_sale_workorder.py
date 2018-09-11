import time
from openerp.osv import osv, fields
import logging

logger = logging.getLogger(__name__)


class WizardReportWorkorders(osv.osv_memory):
    _name = 'wizard.report.workorders'
    _description = 'Report Workorders'

    _columns = {
        'date_start': fields.date('Start Date', required=True),
        'date_end': fields.date('End Date', required=True),
        'iface_summary': fields.boolean('Summary'),
    }

    def print_report(self, cr, uid, ids, context=None):
        print "Print Sale WorkOrders"
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        res = self.read(cr, uid, ids, ['date_start', 'date_end', 'iface_summary'], context=context)
        res = res and res[0] or {}
        datas['form'] = res
        if res.get('id', False):
            datas['ids'] = [res['id']]
        if res['iface_summary']:
            return self.pool['report'].get_action(cr, uid, [], 'jakc_sale.report_workorder_summary', data=datas,context=context)
        else:
            return self.pool['report'].get_action(cr, uid, [], 'jakc_sale.report_workorders', data=datas, context=context)