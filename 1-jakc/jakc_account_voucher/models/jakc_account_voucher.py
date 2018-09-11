from openerp import fields, models, api, _
from openerp.exceptions import Warning, ValidationError, UserError
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class AccountVoucher(models.Model):
    _inherit = 'account.voucher'

    printed_num = fields.Integer("Printed #", readonly=True)
    other_name = fields.Char("No Reference", readonly=True)
    reference = fields.Char("Reference", size=200)

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


class AccountVoucerLine(models.Model):
    _inherit = 'account.voucher.line'

    @api.multi
    def product_id_change(self, product_id, partner_id=False, price_unit=False, company_id=None, currency_id=None, type=None):
        context = self._context
        company_id = company_id if company_id is not None else context.get('company_id', False)
        company = self.env['res.company'].browse(company_id)
        currency = self.env['res.currency'].browse(currency_id)

        #if not partner_id:
        #    raise UserError(_("You must first select a partner!"))

        part = self.env['res.partner'].browse(partner_id)
        if part.lang:
            self = self.with_context(lang=part.lang)

        product = self.env['product.product'].browse(product_id)
        fpos = part.property_account_position_id
        account = self._get_account(product, fpos, type)
        values = {
            'name': product.partner_ref,
            'account_id': account.id,
        }

        if type == 'purchase':
            values['price_unit'] = price_unit or product.standard_price
            taxes = product.supplier_taxes_id or account.tax_ids
            if product.description_purchase:
                values['name'] += '\n' + product.description_purchase
        else:
            values['price_unit'] = price_unit or product.lst_price
            taxes = product.taxes_id or account.tax_ids
            if product.description_sale:
                values['name'] += '\n' + product.description_sale

        values['tax_ids'] = taxes.ids

        if company and currency:
            if company.currency_id != currency:
                if type == 'purchase':
                    values['price_unit'] = price_unit or product.standard_price
                values['price_unit'] = values['price_unit'] * currency.rate

        return {'value': values, 'domain': {}}