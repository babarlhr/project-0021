from datetime import datetime
from datetime import timedelta
import pytz
import time
from openerp import models, fields, api, _
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
            timestamp = datetime.strptime(form[date_field] + ' 00:00:00',
                                                   tools.DEFAULT_SERVER_DATETIME_FORMAT) + timedelta(**delta)
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
    _name = 'report.jakc_sale.report_workorders'
    _inherit = 'report.abstract_report'
    _template = 'jakc_sale.report_workorders'
    _wrapped_report_class = sale_workorders


class sale_workorder_summary(report_sxw.rml_parse):

    def _get_utc_time_range(self, form):
        user = self.pool['res.users'].browse(self.cr, self.uid, self.uid)
        tz_name = user.tz or self.localcontext.get('tz') or 'UTC'
        user_tz = pytz.timezone(tz_name)
        between_dates = {}

        for date_field, delta in {'date_start': {'days': 0}, 'date_end': {'days': 1}}.items():
            timestamp = datetime.strptime(form[date_field] + ' 00:00:00',
                                                   tools.DEFAULT_SERVER_DATETIME_FORMAT) + timedelta(**delta)
            timestamp = user_tz.localize(timestamp).astimezone(pytz.utc)
            between_dates[date_field] = timestamp.strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT)

        return between_dates['date_start'], between_dates['date_end']

    def _get_material_amount(self, sale_order_id):
        sale_order_obj = self.pool.get('sale.order')
        sale_order = sale_order_obj.browse(sale_order_id)
        return sale_order.scheduled_product_amount

    def _get_sale_order_summary(self, form):
        sale_order_obj = self.pool.get('sale.order')
        day_start = datetime.strptime(form['date_start'], '%Y-%m-%d')
        day_end = datetime.strptime(form['date_end'], '%Y-%m-%d')
        day = timedelta(days=1)
        workorder_summary_all = []

        while day_start <= day_end:
            args = [('iface_workorder','=', True),
                    ('date_order', '>=', day_start.strftime('%Y-%m-%d') + ' 00:00:00'),
                    ('date_order', '<=', day_start.strftime('%Y-%m-%d') + ' 23:59:00'),]
            sale_order_ids = sale_order_obj.search(self.cr, self.uid, args)
            total_jasa = 0
            total_or = 0
            total_material = 0
            total_spk = 0
            total_panel = 0
            total_sparepart = 0
            total_personal = 0
            total_insurance = 0
            for order in sale_order_obj.browse(self.cr, self.uid, sale_order_ids):
                total_jasa = total_jasa + order.amount_total
                total_or = total_or + order.or_amount
                total_material = total_material + order.scheduled_product_amount
                total_spk = total_spk + 1
                total_panel = total_panel + order.production_count
                total_sparepart = total_sparepart + order.sparepart_line_count
                if order.iface_insurance:
                    total_insurance = total_insurance + 1
                else:
                    total_personal = total_personal + 1

            workorder_summary = {}
            workorder_summary.update({'date_order': day_start})
            workorder_summary.update({'total_jasa': total_jasa})
            workorder_summary.update({'total_or': total_or})
            workorder_summary.update({'total_material': total_material})
            workorder_summary.update({'total_spk': total_spk})
            workorder_summary.update({'total_panel': total_panel})
            workorder_summary.update({'total_sparepart': total_sparepart})
            workorder_summary.update({'total_personal': total_personal})
            workorder_summary.update({'total_insurance': total_insurance})
            workorder_summary_all.append(workorder_summary)
            day_start = day_start + day

        return workorder_summary_all

    def __init__(self, cr, uid, name, context):
        super(sale_workorder_summary, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            '_get_sale_order_summary': self._get_sale_order_summary,
        })


class report_workorder_summary(osv.AbstractModel):
    _name = 'report.jakc_sale.report_workorder_summary'
    _inherit = 'report.abstract_report'
    _template = 'jakc_sale.report_workorder_summary'
    _wrapped_report_class = sale_workorder_summary

