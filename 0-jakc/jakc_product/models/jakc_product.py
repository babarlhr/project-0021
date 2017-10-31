from openerp import fields, models, api, _
from openerp.exceptions import Warning
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):

    _inherit = 'product.template'

    iface_worktype = fields.Boolean('Is Work Type', default=False)