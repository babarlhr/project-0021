##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
from datetime import datetime
from dateutil.relativedelta import relativedelta

from openerp.report import report_sxw
from openerp.tools.translate import _
from openerp.osv import osv
from openerp import api, models, _
from common_report_header import common_report_header

class report_account_common(report_sxw.rml_parse, common_report_header):
    def __init__(self, cr, uid, name, context):
        super(report_account_common, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'get_periods': self.get_periods,
            'get_lines': self.get_lines,
            'time': time,
        })
        self.context = context
    
    def get_periods(self, data):
        period_ids = []
        if data['form']['used_context'].get('date_from') and data['form']['used_context'].get('date_to'):
            ds = datetime.strptime(data['form']['used_context'].get('date_from'), '%Y-%m-%d')
            while ds.strftime('%Y-%m-%d')<data['form']['used_context'].get('date_to'):
                de = ds + relativedelta(months=1, days=-1)
                if de.strftime('%Y-%m-%d')>data['form']['used_context'].get('date_to'):
                    de = datetime.strptime(data['form']['used_context'].get('date_to'), '%Y-%m-%d')
                period_ids.append(ds.strftime('%b-%Y'))
                ds = ds + relativedelta(months=1)
        return period_ids
    
    def get_lines(self, data):
        #print "get_lines------------->>",data['form']['date_from']#, self.get_account_lines
        lines = []
        account_obj = self.pool.get('account.account')
        currency_obj = self.pool.get('res.currency')
        financial_obj = self.pool.get('account.financial.report')
        account_report = financial_obj.browse(self.cr, self.uid, data['form']['account_report_id'][0])
        child_reports = account_report._get_children_by_order()
        #print "---child_reports---",child_reports
        #ADD THIS FUNCTION TO MAKE HIRARCY
        childs = []
        childs_report_method = []
        for child in child_reports:
            childs.append(child.id)
            childs_report_method.append(child.report_method)
        child_ids = financial_obj.search(self.cr, self.uid, [('id', 'in', childs)], order='sequence, code asc')
        #print "=----child_ids----==",child_ids
        #context.update(data.get('used_context'))
        child_reports = financial_obj.browse(self.cr, self.uid, child_ids)
        #print "==child_reports===",child_reports
        res = self._compute_report_balance(child_reports, context=data['form']['used_context'])
        #print "===res====",res
        #res = self.with_context(data.get('used_context'))._compute_report_balance(child_reports)
        if data['form']['enable_filter'] and not data['form']['multi_period']:
            comparison_res = self._compute_report_balance(child_reports, context=data['form']['comparison_context'])
            for report_id, value in comparison_res.items():
                res[report_id]['comp_bal'] = value['balance']
                report_acc = res[report_id].get('account')
                #print "====res[report_id]====",res[report_id]
                if report_acc:
                    for account_id, val in comparison_res[report_id].get('account').items():
                        #print "===account_id==",account_id,val
                        report_acc[account_id]['comp_bal'] = val['balance']
        multiperiod_res = {}  
        filter_periods = []     
        if data['form']['enable_filter'] and data['form']['multi_period']:
            #print "===multiperiod_res_01==",data['form']['used_context'].get('date_from')
            if data['form']['used_context'].get('date_from') and data['form']['used_context'].get('date_to'):
                date_start = data['form']['used_context'].get('date_from')
                date_end = data['form']['used_context'].get('date_to')
                ds = datetime.strptime(date_start, '%Y-%m-%d')
                while ds.strftime('%Y-%m-%d')<date_end:
                    de = ds + relativedelta(months=1, days=-1)
                    if de.strftime('%Y-%m-%d')>date_end:
                        de = datetime.strptime(date_end, '%Y-%m-%d')
                    filter_periods.append(ds.strftime('%b-%Y'))
                    #create loop monthly here
                    #print "=====----======",childs,childs_report_method,data['form']['multiperiod_context']['strict_range']# = False if result['report_method'] == 'balance' else True
                    if 'balance' in childs_report_method:
                        data['form']['multiperiod_context'].update({'date_from': False, 'date_to': de.strftime('%Y-%m-%d')})
                    else:
                        data['form']['multiperiod_context'].update({'date_from': ds.strftime('%Y-%m-%d'), 'date_to': de.strftime('%Y-%m-%d')})
                    multiperiod_res = self._compute_report_balance(child_reports, context=data['form']['multiperiod_context'])
                    #print "====multiperiod_res====",multiperiod_res
                    for report_id, value in multiperiod_res.items():
                        res[report_id]['comp_bal_%s'%str(ds.strftime('%b-%Y'))] = value['balance']
                        report_acc = res[report_id].get('account')
                        #print "====res===>>>>",res[report_id]
                        if report_acc:
                            for account_id, val in multiperiod_res[report_id].get('account').items():
                                #print "===account_id==",account_id,val
                                report_acc[account_id]['comp_bal_%s'%str(ds.strftime('%b-%Y'))] = val['balance']
                    #========================
                    ds = ds + relativedelta(months=1)
        #print "----filter_periods----",filter_periods
        for report in child_reports:
            if report.parent_id:
                #print "==report==",report.account_ids
                report_balance = res[report.id]['balance']
                vals = {
                    'report':report,
                    'code': report.code,
                    'name': report.name,
                    'balance': report_balance * report.sign,#res[report.id]['balance'] * report.sign,
                    'type': 'report',
                    'level': bool(report.style_overwrite) and report.style_overwrite or report.level,
                    'account_type': report.type =='sum' and 'view' or False, #used to underline the financial report balances
                    'account_ids': report.account_ids,
                }
                if data['form']['debit_credit']:
                    vals['debit'] = res[report.id]['debit']
                    vals['credit'] = res[report.id]['credit']
                if data['form']['enable_filter'] and not data['form']['multi_period']:
                    vals['balance_cmp'] = res[report.id]['comp_bal'] * report.sign#self.pool.get('account.financial.report').browse(self.cr, self.uid, report.id, context=data['form']['comparison_context']).balance * report.sign or 0.0
                if data['form']['enable_filter'] and data['form']['multi_period']:
                    vals['filter_periods'] = filter_periods
                    for period in filter_periods:
                        vals['balance_%s'%str(period)] = res[report.id]['comp_bal_%s'%str(period)] * report.sign
                lines.append(vals)
                account_ids = []
                if report.display_detail == 'no_detail':
                    #the rest of the loop is used to display the details of the financial report, so it's not needed here.
                    continue
                #print "---res[report.id].get('account')----",res[report.id]['account'].items()
                if res[report.id].get('account'):
                    for account_id, value in res[report.id]['account'].items():#[(1127, {'credit': 0.0, 'balance': 0.0, 'debit': 0.0}), (1128, {'credit': 0.0, 'balance': 0.0, 'debit': 0.0}), (1129, {'credit': 0.0, 'balance': 0.0, 'debit': 0.0})]:#res[report.id]['account'].items():
                        #if there are accounts to display, we add them to the lines with a level equals to their level in
                        #the COA + 1 (to avoid having them with a too low level that would conflicts with the level of data
                        #financial reports for Assets, liabilities...)
                        #flag = False
                        flag = True
                        account = self.pool.get('account.account').browse(self.cr, self.uid, account_id)
                        #print '===account===',account,account.name,account.code,account.parent_left
                        value_balance = value['balance']
                        vals = {
                            'report':report,
                            'code': account.code,
                            'name': account.name,
                            'balance': value_balance * report.sign or 0.0,#value['balance'] * report.sign or 0.0,
                            'type': 'account',
                            'level': report.account_ids and report.child_level or 5,
                            'account_type': account.internal_type,
                            'account_ids': report.account_ids,
                        }
                        if data['form']['debit_credit']:
                            vals['debit'] = value['debit']
                            vals['credit'] = value['credit']
                            if not account.company_id.currency_id.is_zero(vals['debit']) or not account.company_id.currency_id.is_zero(vals['credit']):
                                flag = True
                        if not account.company_id.currency_id.is_zero(vals['balance']):
                            flag = True
                        if data['form']['enable_filter'] and not data['form']['multi_period']:
                            vals['balance_cmp'] = value['comp_bal'] * report.sign
                            if not account.company_id.currency_id.is_zero(vals['balance_cmp']):
                                flag = True
                        if data['form']['enable_filter'] and data['form']['multi_period']:
                            vals['filter_periods'] = filter_periods
                            for period in filter_periods:
                                vals['balance_%s'%str(period)] = value['comp_bal_%s'%str(period)] * report.sign
                        if flag:
                            lines.append(vals)
        return lines

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
