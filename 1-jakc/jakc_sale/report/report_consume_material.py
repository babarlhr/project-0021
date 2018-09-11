import datetime
import pytz
import time
from openerp import tools
from openerp.osv import osv
from openerp.report import report_sxw


class consume_materials(report_sxw.rml_parse):

    def _get_employee_name(self, employee_id):
        employee_obj = self.pool.get('hr.employee')
        return employee_obj.browse(self.cr, self.uid, employee_id)['name']

    def _get_routing_name(self, routing_id):
        mrp_routing_obj = self.pool.get('mrp.routing')
        return mrp_routing_obj.browse(self.cr, self.uid, routing_id)['name']

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


    def _get_sale_orders(self, form):
        sale_order_obj = self.pool.get('sale.order')
        date_start, date_end = self._get_utc_time_range(form)
        args = [('iface_workorder','=', True),
                ('date_order', '>=', date_start),
                ('date_order', '<', date_end),]
        sale_order_ids = sale_order_obj.search(self.cr, self.uid, args, order='date_order asc')
        #ids = []
        #for sale_order_id  in sale_order_ids:
        #    ids.append(sale_order_id.id)
        return sale_order_ids

    def _get_product(self, product_id):
        product_template_obj = self.pool.get('product.template')
        product = product_template_obj.browse(self.cr, self.uid, product_id)
        return product

    def  _get_sale_order_consume_materials(self, form):
        date_start, date_end = self._get_utc_time_range(form)
        strSQL = """SELECT d.id as product_id, d.name as product_name, sum(a.quantity) as quantity from sale_order_consume_material as a 
                 LEFT JOIN sale_order as b ON a.sale_order_id = b.id  
                 LEFT JOIN product_product as c ON a.product_id = c.id
                 LEFt JOIN product_template as d ON c.product_tmpl_id = d.id
                 WHERE b.date_order BETWEEN '{}' AND '{}'
                 GROUP BY d.id, d.name """.format(date_start, date_end)
        self.cr.execute(strSQL)
        data = self.cr.dictfetchall()
        return data

    def __init__(self, cr, uid, name, context):
        super(consume_materials, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            '_get_sale_orders': self._get_sale_orders,
            '_get_product': self._get_product,
            '_get_sale_order_consume_materials': self._get_sale_order_consume_materials,
        })


class report_consume_materials(osv.AbstractModel):
    _name = 'report.jakc_sale.report_consumematerials'
    _inherit = 'report.abstract_report'
    _template = 'jakc_sale.report_consumematerials'
    _wrapped_report_class = consume_materials


