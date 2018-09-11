from openerp import fields, models, api, _
from openerp.exceptions import Warning
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    allowed_account_ids = fields.Many2many('account.account','rel_res_user_account_account','account_id', 'res_user_id', 'Accounts')

