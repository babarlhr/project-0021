# -*- coding: utf-8 -*-
# Copyright 2010 Thamini S.à.R.L    This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

import time
import xlwt
from openerp.addons.jakc_report_xls.report_xls import report_xls
from openerp.addons.jakc_report_xls.utils import rowcol_to_cell

from account_financial_report import report_account_common

from openerp.tools.translate import _
_column_sizes = [
    ('code', 18),
    ('name', 40), 
    ('jan', 18), 
    ('feb', 18), 
    ('mar', 18), 
    ('apr', 18), 
    ('mei', 18), 
    ('jun', 18), 
    ('jul', 18), 
    ('agt', 18), 
    ('sep', 18),   
    ('okt', 18), 
    ('nov', 18), 
    ('des', 18),   
    ('balance', 18),           
]

class report_account_financial_xls(report_xls):
    column_sizes = [x[1] for x in _column_sizes]
    no_ind = 0
     
    def get_no_index(self):
        self.set_no_index()
        return self.no_ind
     
    def set_no_index(self):
        self.no_ind += 1
        return True

    def generate_xls_report(self, _p, _xs, data, objects, wb):
        #print "--------generate_xls_report----------",_p.company.partner_id.name#['company']
        ws = wb.add_sheet((data['form']['account_report_id'][1]))
        row_pos = 0
        # Column Title Row
        ws.panes_frozen = True
        ws.remove_splits = True
        # set print header/footer
        ws.header_str = self.xls_headers['standard']
        ws.footer_str = self.xls_footers['standard']      
        # Title
        cell_format = _xs['bold']
        cell_style = xlwt.easyxf(_xs['xls_title'])
        cell_style_center = xlwt.easyxf(cell_format + _xs['center'])
        cell_style_left = xlwt.easyxf(cell_format + _xs['left'])
        report_name = _p.company.partner_id.name
        #for header company
        c_specs = [('report_name', 3, 0, 'text', report_name.upper())]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])        
        row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=cell_style_center)
        #header title
        title_name = data['form']['account_report_id'][1]
        c_specs = [('title_name', 3, 0, 'text', title_name.upper())]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])        
        row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=cell_style_center)
        #for header date range
        c_specs = [('date_range', 3, 0, 'text', _p.formatLang(data['form']['date_from'], date=True) + ' - ' + _p.formatLang(data['form']['date_to'], date=True)),]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=cell_style_center)
        # write empty row to define column sizes
        c_sizes = self.column_sizes
        c_specs = [('empty%s' % i, 1, c_sizes[i], 'text', None) for i in range(0, len(c_sizes))]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(ws, row_pos, row_data, set_column_size=True)
        
        cell_format = _xs['bold']
        c_title_cell_style = xlwt.easyxf(cell_format, num_format_str='#,##0.00;(#,##0.00)')
        #ws.set_horz_split_pos(row_pos)
        row_pos += 1
        
        periods = _p.get_periods(data)
        #print "====",periods
        #if not compare & not debit credit
        if not data['form']['enable_filter'] and not data['form']['debit_credit'] and not data['form']['multi_period']:
            c_specs = [
                    ('cd', 1, 0, 'text', 'Code'),
                    ('nm', 1, 0, 'text', 'Name'),
                    ('bl', 1, 0, 'text', 'Balance'),
                ]
            row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
            row_pos = self.xls_write_row(ws, row_pos, row_data, c_title_cell_style)
            ws.horz_split_pos = row_pos
            for account in _p.get_lines(data):
                #print "aaaaa",account['code'],accounts#['report']
                style_font_xls = account['report']['style_font_xls']#_xs[line.financial_id.style_font_xls]
                color_font_xls = account['report']['color_font_xls']#_xs[line.financial_id.color_font_xls]
                color_fill_xls = account['report']['color_fill_xls']#_xs[line.financial_id.color_fill_xls]
                border_xls = account['report']['border_xls']#_xs[line.financial_id.border_xls]
                
                accounts = []
                for acc in account['account_ids']:
                    accounts.append(acc.code)
                    
                if account['code'] in accounts:
                    line_cell_style = xlwt.easyxf(num_format_str='#,##0.00;(#,##0.00)')
                else:
                    line_cell_style = xlwt.easyxf(_xs[style_font_xls] + _xs[color_font_xls] + _xs[color_fill_xls] + _xs[border_xls], num_format_str='#,##0.00;(#,##0.00)')
                if account['name'] == 'SPACE':
                    c_specs = [
                        ('code', 1, 0, 'text', ''),
                        ('name', 1, 0, 'text', ''),
                        ('balance', 1, 0, 'text', ''),
                    ]
                else:
                    c_specs = [
                        ('code', 1, 0, 'text', account['code'] or ''),
                        ('name', 1, 0, 'text', account['name'] not in ('TOTAL','SPACE') and '  '*account['level'] + account['name'] or ''),
                        ('balance', 1, 0, 'number', account['balance'] or 0.0),
                    ]
                row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
                row_pos = self.xls_write_row(ws, row_pos, row_data, line_cell_style)
        #if with debit & credit
        elif data['form']['debit_credit'] and not data['form']['multi_period']:
            c_specs = [
                    ('cd', 1, 0, 'text', 'Code'),
                    ('nm', 1, 0, 'text', 'Name'),
                    ('db', 1, 0, 'text', 'Debit'),
                    ('cr', 1, 0, 'text', 'Credit'),
                    ('bl', 1, 0, 'text', 'Balance'),
                ]
            row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
            row_pos = self.xls_write_row(ws, row_pos, row_data, c_title_cell_style)
            ws.horz_split_pos = row_pos
            for account in _p.get_lines(data):
                style_font_xls = account['report']['style_font_xls']#_xs[line.financial_id.style_font_xls]
                color_font_xls = account['report']['color_font_xls']#_xs[line.financial_id.color_font_xls]
                color_fill_xls = account['report']['color_fill_xls']#_xs[line.financial_id.color_fill_xls]
                border_xls = account['report']['border_xls']#_xs[line.financial_id.border_xls]
                
                accounts = []
                for acc in account['account_ids']:
                    accounts.append(acc.code)
                    
                if account['code'] in accounts:
                    line_cell_style = xlwt.easyxf(num_format_str='#,##0.00;(#,##0.00)')
                else:
                    line_cell_style = xlwt.easyxf(_xs[style_font_xls] + _xs[color_font_xls] + _xs[color_fill_xls] + _xs[border_xls], num_format_str='#,##0.00;(#,##0.00)')
                
                c_specs = [
                    ('code', 1, 0, 'text', account['name'] != 'SPACE' and account['code'] or ''),
                    ('name', 1, 0, 'text', account['name'] not in ('TOTAL','SPACE') and '  '*account['level'] + account['name'] or ''),
                    ('debit', 1, 0, 'number', account['name'] != 'SPACE' and '' or account['debit'] or 0.0),
                    ('credit', 1, 0, 'number', account['name'] != 'SPACE' and '' or account['credit'] or 0.0),
                    ('balance', 1, 0, 'number', account['name'] != 'SPACE' and '' or account['balance'] or 0.0),
                ]
                row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
                row_pos = self.xls_write_row(ws, row_pos, row_data, line_cell_style)
        #if compare with other
        elif data['form']['enable_filter'] and not data['form']['debit_credit'] and not data['form']['multi_period']:
            c_specs = [
                    ('cd', 1, 0, 'text', 'Code'),
                    ('nm', 1, 0, 'text', 'Name'),
                    ('bl', 1, 0, 'text', 'Balance'),
                    ('blcm', 1, 0, 'text', data['form']['label_filter']),
                ]
            row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
            row_pos = self.xls_write_row(ws, row_pos, row_data, c_title_cell_style)
            ws.horz_split_pos = row_pos
            for account in _p.get_lines(data):
                style_font_xls = account['report']['style_font_xls']#_xs[line.financial_id.style_font_xls]
                color_font_xls = account['report']['color_font_xls']#_xs[line.financial_id.color_font_xls]
                color_fill_xls = account['report']['color_fill_xls']#_xs[line.financial_id.color_fill_xls]
                border_xls = account['report']['border_xls']#_xs[line.financial_id.border_xls]
                accounts = []
                for acc in account['account_ids']:
                    accounts.append(acc.code)
                    
                if account['code'] in accounts:
                    line_cell_style = xlwt.easyxf(num_format_str='#,##0.00;(#,##0.00)')
                else:
                    line_cell_style = xlwt.easyxf(_xs[style_font_xls] + _xs[color_font_xls] + _xs[color_fill_xls] + _xs[border_xls], num_format_str='#,##0.00;(#,##0.00)')
                
                c_specs = [
                    ('code', 1, 0, 'text', account['name'] != 'SPACE' and account['code'] or ''),
                    ('name', 1, 0, 'text', account['name'] not in ('TOTAL','SPACE') and '  '*account['level'] + account['name'] or ''),
                    ('balance', 1, 0, 'number', account['name'] != 'SPACE' and '' or account['balance'] or 0.0),
                    ('balance_cmp', 1, 0, 'number', account['name'] != 'SPACE' and '' or account['balance_cmp'] or 0.0),
                ]
                row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
                row_pos = self.xls_write_row(ws, row_pos, row_data, line_cell_style)
        elif data['form']['multi_period'] and not data['form']['debit_credit']:
            c_specs = [('cd', 1, 0, 'text', 'Code'),
                       ('nm', 1, 0, 'text', 'Name')]
            for pbl in periods:
                c_specs += [('pbl%s'%str(pbl), 1, 0, 'text', '%s'%str(pbl))]
            if data['form']['report_method'] != 'balance':
                c_specs += [('bl', 1, 0, 'text', 'TOTAL')]
            
            row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
            row_pos = self.xls_write_row(ws, row_pos, row_data, c_title_cell_style)
            ws.horz_split_pos = row_pos
            for account in _p.get_lines(data):
                style_font_xls = account['report']['style_font_xls']#_xs[line.financial_id.style_font_xls]
                color_font_xls = account['report']['color_font_xls']#_xs[line.financial_id.color_font_xls]
                color_fill_xls = account['report']['color_fill_xls']#_xs[line.financial_id.color_fill_xls]
                border_xls = account['report']['border_xls']#_xs[line.financial_id.border_xls]
                accounts = []
                for acc in account['account_ids']:
                    accounts.append(acc.code)
                    
                if account['code'] in accounts:
                    line_cell_style = xlwt.easyxf(num_format_str='#,##0.00;(#,##0.00)')
                else:
                    line_cell_style = xlwt.easyxf(_xs[style_font_xls] + _xs[color_font_xls] + _xs[color_fill_xls] + _xs[border_xls], num_format_str='#,##0.00;(#,##0.00)')
                
                c_specs = [
                    ('code', 1, 0, 'text', account['name'] != 'SPACE' and account['code'] or ''),
                    ('name', 1, 0, 'text', account['name'] not in ('TOTAL','SPACE') and '  '*account['level'] + account['name'] or ''),      
                ]
                for pbl in periods:
                    c_specs += [('balance_%s'%str(pbl), 1, 0, 'number', account['name'] != 'SPACE' and '' or account['balance_%s'%str(pbl)] or 0.0)]
                if data['form']['report_method'] != 'balance':
                    c_specs += [('balance', 1, 0, 'number', account['name'] != 'SPACE' and '' or account['balance'] or 0.0)]
                row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
                row_pos = self.xls_write_row(ws, row_pos, row_data, line_cell_style)
        pass

report_account_financial_xls('report.account.financial.profit.loss.xls',
                  'accounting.report',
                  parser=report_account_common)  