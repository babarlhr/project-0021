from datetime import datetime, timedelta
from openerp import SUPERUSER_ID
from openerp import api, fields, models, _
import openerp.addons.decimal_precision as dp
from openerp.exceptions import UserError
from openerp.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
import logging


class ResPartner(models.Model):
    _inherit = 'res.partner'

    iface_surveyor = fields.Boolean('Is Surveyor')
    iface_insurance = fields.Boolean('Is Insurance')
    or_fee = fields.Float('OR', default=0.0)
