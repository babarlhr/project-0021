from openerp import api, fields, models
from openerp.exceptions import  ValidationError, UserError, Warning
from datetime import datetime

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    printed_num = fields.Integer('Printed #', readonly=True)
    delivery_state = fields.Selection([('draft','Not Sent'),('sent','Sent'),('delivered','Delivered')],'Delivery', default='draft', readonly=True)

    @api.multi
    def invoice_print(self):
        res = super(AccountInvoice, self).invoice_print()
        printed_num = self.printed_num + 1
        self.write({'printed_num': printed_num})
        return res


class AccountInvoiceDelivery(models.Model):
    _name = 'account.invoice.delivery'

    @api.one
    def trans_sent(self):
        for delivery in self:
            delivery.state = 'sent'
            for account_invoice in delivery.account_invoice_ids:
                account_invoice.delivery_state = 'sent'

    @api.one
    def trans_delivered(self):
        for delivery in self:
            delivery.state = 'delivered'
            for account_invoice in delivery.account_invoice_ids:
                account_invoice.delivery_state = 'delivered'

    name = fields.Char('Name', size=100, required=True)
    date = fields.Date('Delivery Date', required=True, default=datetime.now())
    messenger_id = fields.Many2one('hr.employee','Messenger', required=True)
    attachment = fields.Binary('Document', required=False)
    attachment_filename = fields.Char('Document Filename', size=100, readonly=False)
    account_invoice_ids = fields.Many2many('account.invoice','delivery_per_invoice_wizard', 'account_invoice_id', 'delivery_id', 'Invoices')
    state = fields.Selection([('draft','New'),('sent','Sent to Customer'),('delivered','Delivered')],'Status', default='draft', readonly=True)

    @api.multi
    def unlink(self):
        if self.state == 'draft':
            return super(AccountInvoiceDelivery,self).unlink()
        else:
            raise ValidationError('Cannot Deleted, Delivery Already Process Succesfully')