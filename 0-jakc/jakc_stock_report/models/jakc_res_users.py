from openerp import api, fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    iface_receive_notification = fields.Boolean('Receive Notification')

