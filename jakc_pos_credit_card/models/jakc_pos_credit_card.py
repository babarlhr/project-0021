# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import sets

from openerp import models, fields, api, _

_logger = logging.getLogger(__name__)

class account_bank_statement_line(models.Model):
    _inherit = "account.bank.statement.line"
    cardnumber = fields.Char(string='Card Number', size=50)
    cardowner = fields.Char(stirng='Card Owner', size=100)
    
class account_journal(models.Model):
    _inherit = "account.journal"
    iface_card = fields.Boolean(string='Debit or Credit Card', default=False)
    
class pos_order_card(models.Model):
    _inherit = "pos.order"

    @api.model
    def _payment_fields(self, ui_paymentline):
        fields = super(pos_order_card, self)._payment_fields(ui_paymentline)

        fields.update({
            'card_number': ui_paymentline.get('cardnumber'),
            'card_owner': ui_paymentline.get('cardowner'),
        })

        return fields

    @api.model
    def add_payment(self, order_id, data):
        statement_id = super(pos_order_card, self).add_payment(order_id, data)
        statement_lines = self.env['account.bank.statement.line'].search([('statement_id', '=', statement_id),
                                                                         ('pos_statement_id', '=', order_id),
                                                                         ('journal_id', '=', data['journal']),
                                                                         ('amount', '=', data['amount'])])

        # we can get multiple statement_lines when there are >1 credit
        # card payments with the same amount. In that case it doesn't
        # matter which statement line we pick, just pick one that
        # isn't already used.
        print data
        for line in statement_lines:
            line.cardnumber = data.get('card_number')
            line.cardowner = data.get('card_owner')
            #line.cardnumber = "1111"
            #line.cardowner = "Wahyu"
            
        return statement_id
    
    