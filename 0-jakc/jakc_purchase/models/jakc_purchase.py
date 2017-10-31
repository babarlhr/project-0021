from openerp import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    printed_num = fields.Integer('Printed #', readonly=True)


    @api.multi
    def print_purchase_order(self):
        res = self.env['report'].get_action(self, 'jakc_purchase.report_purchaseorder_custom')
        printed_num = self.printed_num + 1
        self.write({'printed_num': printed_num})
        return res