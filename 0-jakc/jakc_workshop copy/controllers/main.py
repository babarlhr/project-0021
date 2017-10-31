import json
import logging
import werkzeug
import werkzeug.utils
from datetime import datetime
from math import ceil

from openerp import SUPERUSER_ID
from openerp.addons.web import http
from openerp.addons.web.http import request
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
        return request.website.render('jakc_workshop.workshop_workorder_by_plat',
                                      { 'workorder_ids':["WO0003","WO004"]})


    @http.route('/workshop/workorder/detail/<string:spk>', type='http', auth='user', website=True)
    def workorder_detail(self, spk=None):
        partner_vehicle_obj = http.request.env['partner.vehicle']
        sale_order_obj = http.request.env['sale.order']
        sale_order_args = [('name', '=', spk)]
        sale_order_ids = sale_order_obj.search(sale_order_args)
        datas = {}
        datas.update({'workorder': sale_order_ids[0]})

        return request.website.render('jakc_workshop.workshop_workorder_detail', datas)