from datetime import datetime, timedelta
from openerp import SUPERUSER_ID
from openerp import api, fields, models, _
import openerp.addons.decimal_precision as dp
from openerp.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
import logging


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ProcurementOrder(models.Model):
    _inherit = ['procurement.order']

    sale_order_id = fields.Many2one('sale.order','Sale Order', related='sale_line_id.order_id', readonly=True)
    partner_vehicle_id = fields.Many2one('partner.vehicle', related='sale_order_id.partner_vehicle_id', readonly=True, string='Vehicle')

    def make_mo(self, cr, uid, ids, context=None):
        """ Make Manufacturing(production) order from procurement
        @return: New created Production Orders procurement wise
        """
        res = {}
        production_obj = self.pool.get('mrp.production')
        procurement_obj = self.pool.get('procurement.order')
        for procurement in procurement_obj.browse(cr, uid, ids, context=context):
            if self.check_bom_exists(cr, uid, [procurement.id], context=context):
                # create the MO as SUPERUSER because the current user may not have the rights to do it (mto product launched by a sale for example)
                vals = self._prepare_mo_vals(cr, uid, procurement, context=context)
                produce_id = production_obj.create(cr, SUPERUSER_ID, vals,
                                                   context=dict(context, force_company=procurement.company_id.id))
                res[procurement.id] = produce_id
                self.write(cr, uid, [procurement.id], {'production_id': produce_id})
                self.production_order_create_note(cr, uid, procurement, context=context)
                production_obj.action_compute(cr, uid, [produce_id],
                                              properties=[x.id for x in procurement.property_ids])
                production_obj.signal_workflow(cr, uid, [produce_id], 'button_confirm')
                production_obj.action_assign(cr, uid, [produce_id], context=context)
            else:
                res[procurement.id] = False
                self.message_post(cr, uid, [procurement.id], body=_("No BoM exists for this product!"), context=context)
        return res