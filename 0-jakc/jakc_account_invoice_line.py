from openerp import models, fields, api, _
import openerp.addons.decimal_precision as dp


class account_invoice_line(models.Model):
    _inherit = 'account.invoice.line'

    lot_id = fields.Many2one('stock.production.lot', 'Lot', copy=False)
    
