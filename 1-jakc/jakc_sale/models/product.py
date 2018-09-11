from openerp import fields, models, api, _
from openerp.exceptions import Warning
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):

    _inherit = 'product.template'

    fee_percentage = fields.Float('Fee Percentage', default=25)
    iface_paint = fields.Boolean('Paint', default=False)
