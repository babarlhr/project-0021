import datetime
import pytz
import time
from openerp import tools
from openerp.osv import osv
from openerp.report import report_sxw



class sale_workorders(report_sxw.rml_parse):

    def _get_utc_time_range(self, form):
        user = self.pool['res.users'].browse(self.cr, self.uid, self.uid)
        tz_name = user.tz or self.localcontext.get('tz') or 'UTC'
        user_tz = pytz.timezone(tz_name)
        between_dates = {}

        for date_field, delta in {'date_start': {'days': 0}, 'date_end': {'days': 1}}.items():
            timestamp = datetime.datetime.strptime(form[date_field] + ' 00:00:00',
                                                   tools.DEFAULT_SERVER_DATETIME_FORMAT) + datetime.timedelta(**delta)
            timestamp = user_tz.localize(timestamp).astimezone(pytz.utc)
            between_dates[date_field] = timestamp.strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT)

        return between_dates['date_start'], between_dates['date_end']

    def _get_material_amount(self, sale_order_id):
        sale_order_obj = self.pool.get('sale.order')
        sale_order = sale_order_obj.browse(sale_order_id)
        return sale_order.scheduled_product_amount

    def _get_sale_orders(self, form):
        sale_order_obj = self.pool.get('sale.order')
        date_start, date_end = self._get_utc_time_range(form)
        args = [('iface_workorder','=', True),
                ('date_order', '>=', date_start),
                ('date_order', '<', date_end),]
        sale_order_ids = sale_order_obj.search(self.cr, self.uid, args, order='date_order asc')
        sale_orders = sale_order_obj.browse(self.cr, self.uid, sale_order_ids)
        return sale_orders

    def __init__(self, cr, uid, name, context):
        super(sale_workorders, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            '_get_sale_orders': self._get_sale_orders,
            '_get_material_amount': self._get_material_amount,
        })


class report_workorders(osv.AbstractModel):
    _name = 'report.jakc_sale.report_workorderr'
    _inherit = 'report.abstract_report'
    _template = 'jakc_sale.report_workorderr'
    _wrapped_report_class = sale_workorders


