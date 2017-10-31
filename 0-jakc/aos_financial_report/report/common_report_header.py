# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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
from datetime import date, datetime, timedelta
from openerp.tools.translate import _
from openerp import api, models

from openerp.tools import float_is_zero
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

# Mixin to use with rml_parse, so self.pool will be defined.
class common_report_header(object):
    #FOR FINANCIAL REPORT
    def _compute_account_balance(self, accounts, context=None):
        """ compute the balance, debit and credit for the provided accounts
        """
        mapping = {
            'balance': "COALESCE(SUM(debit),0) - COALESCE(SUM(credit), 0) as balance",
            'debit': "COALESCE(SUM(debit), 0) as debit",
            'credit': "COALESCE(SUM(credit), 0) as credit",
        }

        res = {}
        #print "===res=====11111====",res
        for account in accounts:
            res[account.id] = dict((fn, 0.0) for fn in mapping.keys())
            #print "----resssss",account,res[account.id]
        #print "====row=====",accounts
        if accounts:
            tables, where_clause, where_params = self.pool.get('account.move.line')._query_get(self.cr, self.uid, context=context)
            #print "tables===",tables
            #print "where_clause===",where_clause
            #print "where_params===",where_params
            tables = tables.replace('"', '') if tables else "account_move_line"
            wheres = [""]
            if where_clause.strip():
                wheres.append(where_clause.strip())
            filters = " AND ".join(wheres)
            request = "SELECT account_id as id, " + ', '.join(mapping.values()) + \
                       " FROM " + tables + \
                       " WHERE account_id IN %s " \
                            + filters + \
                       " GROUP BY account_id"
            params = (tuple(accounts._ids),) + tuple(where_params)
            self.cr.execute(request, params)
            for row in self.cr.dictfetchall():
                res[row['id']] = row
        return res#{1127: {'credit': 0.0, 'balance': 0.0, 'debit': 0.0}, 1128: {'credit': 0.0, 'balance': 0.0, 'debit': 0.0}, 1129: {'credit': 0.0, 'balance': 0.0, 'debit': 0.0}}

    def _compute_report_balance(self, reports, context=None):
        '''returns a dictionary with key=the ID of a record and value=the credit, debit and balance amount
           computed for this record. If the record is of type :
               'accounts' : it's the sum of the linked accounts
               'account_type' : it's the sum of leaf accoutns with such an account_type
               'account_report' : it's the amount of the related report
               'sum' : it's the sum of the children of this record (aka a 'view' record)'''
        res = {}
        fields = ['balance', 'debit', 'credit']
        #print "==_compute_report_balance====",reports
        for report in reports:
            #print "======",report.type,report.name
            if report.id in res:
                continue
            res[report.id] = dict((fn, 0.0) for fn in fields)
            if report.type == 'accounts':
                # it's the sum of the linked accounts
                #print "===report.account_ids==",report.account_ids
                res[report.id]['account'] = self._compute_account_balance(report.account_ids, context=context)
                #print "====res[report.id]['account']====",res[report.id]['account']
                for value in res[report.id]['account'].values():
                    for field in fields:
                        res[report.id][field] += value.get(field)
            elif report.type == 'account_type':
                # it's the sum the leaf accounts with such an account type
                accounts_ids = self.pool.get('account.account').search(self.cr, self.uid, [('user_type_id', 'in', report.account_type_ids.ids)])
                accounts = self.pool.get('account.account').browse(self.cr, self.uid, accounts_ids)
                res[report.id]['account'] = self._compute_account_balance(accounts, context=context)
                for value in res[report.id]['account'].values():
                    for field in fields:
                        res[report.id][field] += value.get(field)
            elif report.type in ('account_report','account_report_monthly') and report.account_report_ids:
                #print "---context.get('date_from')---",context
                # it's the amount of the linked report
                context_retain_earning = context.copy()
                if report.account_report_id and report.account_report_id.date_range_type == 'last_year':
                    #date_end = datetime.strptime(context_retain_earning.get('date_from'), DEFAULT_SERVER_DATE_FORMAT).date()
                    #date_end_of_year = date(date_end.year, date_end.month, date_end.day)+timedelta(days=-1)
                    #print "---date_end_of_year----",date_end_of_year
                    context_retain_earning.update({'date_from': False, 'date_to': '2015-12-31'})
                res1 = self._compute_report_balance(report.account_report_id, context=context_retain_earning)
                for key, value in res1.items():
                    for field in fields:
                        res[report.id][field] += value[field]    
                #print "==_compute_report_balance===",report.name,report.account_report_id.name
                res2 = self._compute_report_balance(report.account_report_ids, context=context)
                for key, value in res2.items():
                    for field in fields:
                        res[report.id][field] += value[field]
            elif report.type == 'sum':
                # it's the sum of the children of this account.report
                res2 = self._compute_report_balance(report.children_ids, context=context)
                #print "====res2====",res2
                for key, value in res2.items():
                    for field in fields:
                        res[report.id][field] += value[field]
        return res
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
