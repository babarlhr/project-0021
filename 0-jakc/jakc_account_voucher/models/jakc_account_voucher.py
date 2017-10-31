from openerp import fields, models, api, _
from openerp.exceptions import Warning
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class AccountVoucher(models.Model):
    _inherit = 'account.voucher'

    printed_num = fields.Integer("Printed #", readonly=True)
    other_name = fields.Char("No Reference", readonly=True)
    reference = fields.Char("Reference", size=10)

    @api.multi
    def voucher_print(self):
        """ Print the invoice and mark it as sent, so that we can see more
            easily the next step of the workflow
        """
        self.ensure_one()
        printed_num = self.printed_num + 1
        self.write({'printed_num': printed_num})
        return self.env['report'].get_action(self, 'jakc_account_voucher.report_accountvoucher')


    @api.model
    def create(self, vals):
        user = self.env['res.users'].browse(self.env.uid)

        if len(user.allowed_account_ids) > 0:
            allow_account = False
            for allowed_account_id in user.allowed_account_ids:
                if vals.get('account_id') == allowed_account_id.id:
                    allow_account = True
                    break

            if not allow_account:
                raise Warning('Account Not Allowed')

        return super(AccountVoucher, self).create(vals)

