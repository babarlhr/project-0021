import json
import logging
import werkzeug
import werkzeug.utils
from datetime import datetime
from math import ceil

from openerp import SUPERUSER_ID
from openerp.addons.web import http
from openerp.http import request
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT as DTF, ustr


_logger = logging.getLogger(__name__)


class WebsiteWorkshop(http.Controller):

    @http.route('/workshop/workorder/plat/<string:platnumber>', type='http', auth='public', website=True)
    def workorder_list(self, platnumber=None):
        partner_vehicle_obj = http.request.env['partner.vehicle']
        sale_order_obj = http.request.env['sale.order']

        partner_vehicle_args = [('name','=', platnumber)]
        partner_vehicle = partner_vehicle_obj.search(partner_vehicle_args)[0]
        #if partner_vehicle:

        #workorder_obj = http.request.env['sale.order']
        #args = [('')]
        return request.website.render('jakc_sale.workshop_workorder_by_plat',{ 'workorder_ids':["WO0003","WO004"]})

    @http.route('/workshop/workorder/find', type='http', auth='user', website=True)
    def workorder_find(self):
        return request.website.render('jakc_sale.workshop_workorder_detail_find')

    @http.route('/workshop/workorder/list', type='http', auth='user', website=True)
    def workorder_list(self):
        return request.website.render('jakc_sale.workshop_workorder_list')

    @http.route('/workshop/workorder/detail/<string:spk>', type='http', auth='user', website=True)
    def workorder_detail(self, spk=None):
        datas = {}
        if spk:
            res_users_obj = http.request.env['res.users']
            partner_vehicle_obj = http.request.env['partner.vehicle']
            mrp_production_obj = http.request.env['mrp.production']

            uid = http.request.env.context.get('uid')
            res_user = res_users_obj.browse(uid)
            routing_wc = res_user.company_id.routing_wc
            datas.update({'routing': routing_wc})

            sale_order_obj = http.request.env['sale.order']
            sale_order_args = [('name', '=', spk)]
            sale_order_ids = sale_order_obj.search(sale_order_args)

            datas.update({'workorder': sale_order_ids[0]})

        return request.website.render('jakc_sale.workshop_workorder_detail', datas)