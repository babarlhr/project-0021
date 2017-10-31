from openerp import api, fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    printed_num = fields.Integer('Printed #', readonly=True)

    @api.multi
    def invoice_print(self):
        res = super(AccountInvoice, self).invoice_print()
        printed_num = self.printed_num + 1
        self.write({'printed_num': printed_num})
        return res