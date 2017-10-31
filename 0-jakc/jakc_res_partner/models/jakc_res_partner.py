from openerp import fields, models, api, _
from openerp.exceptions import Warning
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    iface_member = fields.Boolean('Workshop Member', default=lambda self: self._context.get('iface_member'))
    partner_vehicle_ids = fields.One2many('partner.vehicle','partner_id','Vehicles')
    partner_code = fields.Char('Code #', size=10, required=True)

    _sql_constraints = [
        ('uniq_partner_code', 'unique(partner_code)', "A Partner Code already exists. Partner Code must be unique!"),
    ]

