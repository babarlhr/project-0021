from openerp.osv import fields, osv
from openerp.tools.translate import _



class StockConfigSettings(osv.osv_memory):
    _name = 'jakc.stock.config.settings'
    _inherit = 'stock.config.settings'

    _columns = {
        'stock_email' : fields.many2one('res.users', 'Email Notification Recipient'),
    }