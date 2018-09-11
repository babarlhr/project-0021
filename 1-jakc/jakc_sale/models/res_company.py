from datetime import datetime, timedelta
from openerp import SUPERUSER_ID
from openerp import api, fields, models, _
import openerp.addons.decimal_precision as dp
from openerp.exceptions import UserError
from openerp.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
import logging


class ResCompany(models.Model):
    _inherit = 'res.company'

    routing_wc = fields.Many2one('mrp.routing', 'Routing')
    or_product = fields.Many2one('product.product', 'OR')
    or_amount = fields.Float('OR Fee')
    iface_auto_reserve = fields.Boolean('Auto Reserve', default=False)
    add_material_authorized = fields.Many2one('res.users', 'Add Material Authorized')

    warehouse_id = fields.Many2one('stock.warehouse','Warehouse')
    row_material_location_id = fields.Many2one('stock.location','Raw Material Location')
    insurance_location_src_id = fields.Many2one('stock.location','Insurance Source Location')
    insurance_location_dest_id = fields.Many2one('stock.location','Insurance Destination Location')
    production_location_id = fields.Many2one('stock.location', 'Production Location')

    location_id = fields.Many2one('stock.location','Source Location')
    location_dest_id = fields.Many2one('stock.location', 'Destination Location')
    move_type = fields.Selection([('direct','Partial'),('one',' All at once')], 'Delivery Method')
    picking_type_id = fields.Many2one('stock.picking.type','Picking Type')
    production_picking_type_id = fields.Many2one('stock.picking.type','Production Picking Type')
    priority = fields.Selection([('0','Not Urgent'),('1','Normal'),('2','Urgent'),('3','Very Urget')], 'Priority')

    insurance_incoming_picking_type_id = fields.Many2one('stock.picking.type','Insurance Incoming Picking Type')
    insurance_outgoing_picking_type_id = fields.Many2one('stock.picking.type','Insurance Outgoing Picking Type')

    iface_final_cogs = fields.Boolean("Final COGS for Material", default=True)
    cogs_product_category_id = fields.Many2one('product.category','Product Category for COGS')

    material_product_category_id = fields.Many2one('product.category','Bahan Baku')