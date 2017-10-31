# -*- coding: utf-8 -*-

from openerp.osv import expression
from openerp import models, fields, api, _
from openerp.exceptions import UserError, ValidationError

class account_financial_report(models.Model):
    _inherit = "account.financial.report"
    _description = "Account Report"
    _order = "sequence, parent_left asc"
    _parent_order = "code"
    _parent_store = True
    
    code = fields.Char('Code', size=64, required=False, select=1)
    name = fields.Char('Report Name', required=True, translate=True)
    report_method  = fields.Selection([
        ('profit_loss', 'Profit & Loss'),
        ('balance', 'Balance'),
        ('none', 'None'),
        ], 'Report Method', default='none',)
    date_range_type = fields.Selection([
        ('current', 'Current Year'),
        ('last_year', 'Last Year'),
        ('none', 'None'),
        ], 'Date Range Method', default='none',)
    strict_range = fields.Boolean('Strict Range Date')
    parent_left = fields.Integer('Parent Left', select=1)
    parent_right = fields.Integer('Parent Right', select=1)
    account_report_ids = fields.Many2many('account.financial.report', 'account_financial_report_ids', 'report_id', 'account_report_id', 'Report Values')
    type = fields.Selection([
        ('view', 'View'),
        ('sum', 'Balance'),
        ('accounts', 'Accounts'),
        ('account_type', 'Account Type'),
        ('account_report', 'Report Value'),
        ('account_report_monthly', 'Report Value (Monthly)'),
        ], 'Type', default='view')
    child_level = fields.Integer('Child Level')
    style_font_xls = fields.Selection([
        ('normal', 'Normal Text'),
        ('italic', 'Italic Text'),
        ('bold', 'Bold Text'),
        ], 'Report Font Style Excel', default='normal',
        help="You can set up here the format you want this record to be displayed. If you leave the automatic formatting, it will be computed based on the financial reports hierarchy (auto-computed field 'level').")
    color_font_xls = fields.Selection([
        ('colour_index_black', 'Black'),
        ('colour_index_grey', 'Grey'),
        ('colour_index_red', 'Red'),
        ('colour_index_blue', 'Blue'),
        ], 'Report Color Font Style Excel', default='colour_index_black',
        help="You can set up here the format you want this record to be displayed. If you leave the automatic formatting, it will be computed based on the financial reports hierarchy (auto-computed field 'level').")
    color_fill_xls = fields.Selection([
        ('fill_white', 'White'),
        ('fill_blue', 'Blue'),
        ('fill_grey', 'Grey'),
        ], 'Report Fill Style Excel', default='fill_white',
        help="You can set up here the format you want this record to be displayed. If you leave the automatic formatting, it will be computed based on the financial reports hierarchy (auto-computed field 'level').")
    border_xls = fields.Selection([
        ('borders_all', 'All'),
        ('borders_top_bottom', 'Top Bottom'),
        ], 'Report Borders Style Excel', default='borders_all',
        help="You can set up here the format you want this record to be displayed. If you leave the automatic formatting, it will be computed based on the financial reports hierarchy (auto-computed field 'level').")
    #fake_line = fields.One2many('account.fake.line', 'financial_id', 'Lines')

    _sql_constraints = [
        ('code_uniq', 'unique (code)', 'The code of the account must be unique !')
    ]
    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('code', '=ilike', name + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&'] + domain
        accounts = self.search(domain + args, limit=limit)
        return accounts.name_get()
    
#     @api.multi
#     @api.depends('name', 'code')
#     def name_get(self):
#         result = []
#         for account in self:
#             name = account.code + ' ' + account.name
#             result.append((account.id, name))
#         return result
    
class AccountJournal(models.Model):
    _inherit = "account.journal"
    
    type = fields.Selection(selection_add=[('sale_refund', 'Sale Refund'),('purchase_refund', 'Purchase Refund'),('situation', 'Opening/Closing Situation')])
    channel_id = fields.Many2one('mail.channel', string='Channel Notification', required=False)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    
    @api.model
    def _query_get_daily(self, domain=None):
        context = dict(self._context or {})
        domain = domain and safe_eval(domain) or []

        date_field = 'date'
        if context.get('aged_balance'):
            date_field = 'date_maturity'
        if context.get('date_from'):
            domain += [(date_field, '>=', context['date_from'])]
        if context.get('date_to'):
            domain += [(date_field, '<=', context['date_to'])]
#             if not context.get('strict_range'):
#                 domain += ['|', (date_field, '>=', context['date_from']), ('account_id.user_type_id.include_initial_balance', '=', True)]
#             elif context.get('initial_bal'):
#                 domain += [(date_field, '<', context['date_from'])]
#             else:
#                 domain += [(date_field, '>=', context['date_from'])]

        if context.get('journal_ids'):
            domain += [('journal_id', 'in', context['journal_ids'])]

        state = context.get('state')
        if state and state.lower() != 'all':
            domain += [('move_id.state', '=', state)]

        if context.get('company_id'):
            domain += [('company_id', '=', context['company_id'])]

        if 'company_ids' in context:
            domain += [('company_id', 'in', context['company_ids'])]

        if context.get('reconcile_date'):
            domain += ['|', ('reconciled', '=', False), '|', ('matched_debit_ids.create_date', '>', context['reconcile_date']), ('matched_credit_ids.create_date', '>', context['reconcile_date'])]

        where_clause = ""
        where_clause_params = []
        tables = ''
        if domain:
            query = self._where_calc(domain)
            tables, where_clause, where_clause_params = query.get_sql()
        return tables, where_clause, where_clause_params
    
# class AccountFakeLine(models.Model):
#     _name = 'account.fake.line'
#     _description = 'Account Lines'
#      
#     name = fields.Selection([
#         ('profit_loss', 'Profit & Loss'),
#         ('balance', 'Balance'),
#         ('none', 'None'),
#         ], 'Report Type', default='profit_loss',)
#     financial_id = fields.Many2one('account.financial.report', 'Financial Report')
#     date = fields.Date('Date From')
#     balance = fields.Float('Balance', digits=(16, 2))