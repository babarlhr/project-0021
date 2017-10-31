
import time
from openerp import api, fields, models
from __builtin__ import True

class AccountingReport(models.TransientModel):
    _inherit = "accounting.report"
    _description = "Accounting Report"
    
    flag = fields.Boolean(string='Include Zero Balance', default=True)
    multi_period = fields.Boolean(string='Multi Period', default=False)
    report_method  = fields.Selection([
        ('profit_loss', 'Profit & Loss'),
        ('balance', 'Balance'),
        ('none', 'None'),
        ], 'Report Method')
    
    @api.multi
    @api.onchange('account_report_id')
    def onchange_account_report_id(self):
        values = {
            'report_method': 'none',
        }
        if self.account_report_id.report_method:
            values['report_method'] = self.account_report_id.report_method
        self.update(values)
    
    def _build_contexts(self, data):
        result = super(AccountingReport, self)._build_contexts(data)
        result['report_method'] = data['form']['report_method'] or 'none'
        result['strict_range'] = False if result['report_method'] == 'balance' else True
        #print "====_build_contexts===",result
        return result
    
    def _build_comparison_context(self, data):
        result = super(AccountingReport, self)._build_comparison_context(data)
        result['report_method'] = data['form']['report_method'] or 'none'
        if data['form']['filter_cmp'] == 'filter_date':
            result['date_from'] = data['form']['date_from_cmp']
            result['date_to'] = data['form']['date_to_cmp']
            result['strict_range'] = False if result['report_method'] == 'balance' else True
        #print "====_build_comparison_context===",result
        return result
    
    def _build_multiperiod_context(self, data):
        result = {}
        result['journal_ids'] = 'journal_ids' in data['form'] and data['form']['journal_ids'] or False
        result['state'] = 'target_move' in data['form'] and data['form']['target_move'] or ''
        result['report_method'] = data['form']['report_method'] or 'none'
        result['strict_range'] = False if result['report_method'] == 'balance' else True
        return result
    
    def xls_export(self, cr, uid, ids, context=None):
        context = context or {}
        if context.get('xls_export'):
            # we update form with display account value
            datas = {'ids': context.get('active_ids', [])}
            datas['model'] = 'accounting.report'
            datas['form'] = self.read(cr, uid, ids, ['date_from', 'date_to', 'strict_range', 'state', 'journal_ids', 
                                                     'date_from_cmp', 'debit_credit', 'date_to_cmp', 'filter_cmp', 'account_report_id', 'enable_filter', 'label_filter', 'target_move', 
                                                     'flag', 'multi_period', 'report_method'
                                                    ])[0]
            used_context = self._build_contexts(datas)
            datas['form']['used_context'] = dict(used_context, lang=context.get('lang', 'en_US'))
            comparison_context = self._build_comparison_context(datas)
            datas['form']['comparison_context'] = comparison_context
            #FILTER DATE MULTI PERIOD
            multiperiod_context = self._build_multiperiod_context(datas)
            datas['form']['multiperiod_context'] = multiperiod_context
            #print "====multiperiod_context===wizard===",multiperiod_context
            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'account.financial.profit.loss.xls',
                'datas': datas
            }