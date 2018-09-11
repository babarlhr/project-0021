import time
from openerp import tools
from operator import itemgetter
import openerp.addons.decimal_precision as dp
from datetime import date, datetime, timedelta
from openerp.osv import fields, osv



class account_account(osv.osv):
    _inherit = "account.account"


    def _get_child_ids(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        for record in self.browse(cr, uid, ids, context=context):
            if record.child_parent_ids:
                result[record.id] = [x.id for x in record.child_parent_ids]
            else:
                result[record.id] = []
            if record.child_consol_ids:
                for acc in record.child_consol_ids:
                    if acc.id not in result[record.id]:
                        result[record.id].append(acc.id)
        return result

    
    def _get_children_and_consol(self, cr, uid, ids, context=None):
        # Ugly Code
        anak = []
        acc = self.browse(cr, uid, ids)
        for x in acc.child_id:
            anak.append(x.id)
            for i in x.child_id:
                anak.append(i.id)
                for o in i.child_id:
                    anak.append(o.id)
                    for u in o.child_id:
                        anak.append(u.id)
                        for a in u.child_id:
                            anak.append(a.id)
        return anak

    
    _columns = {
                'jenis': fields.related('user_type_id', 'name', type='char', string="Type", store=True, readonly=True),
                'parent_id': fields.many2one('account.account', 'Parent', ondelete='cascade', domain=[('jenis', '=', 'View')]),
                'child_id': fields.function(_get_child_ids, type='many2many', relation="account.account", string="Child Accounts"),
                'child_consol_ids': fields.many2many('account.account', 'account_account_consol_rel', 'child_id', 'parent_id', 'Consolidated Children'),
                'child_parent_ids': fields.one2many('account.account','parent_id','Children'),   
    }
    


    def onchange_parent(self, cr, uid, ids, acc):
        val = self.browse(cr, uid, ids)
        if val:
            if acc in self._get_children_and_consol(cr, uid, ids):
                return {'value': {'parent_id': False}, 'warning': {'title': 'Perhatian', 'message': 'Hirarki Recursive'}}
    

class AccountAccountTemplate(osv.osv):
    _inherit = "account.account.template"
    _columns = {
                'parent_id': fields.many2one('account.account.template', 'Parent Account Template', ondelete='cascade'),
    }
    
    



# account.account
#     def __compute(self, cr, uid, ids, field_names, arg=None, context=None, query='', query_params=()):
#         mapping = {
#             'balance': "COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) as balance",
#             'debit': "COALESCE(SUM(l.debit), 0) as debit",
#             'credit': "COALESCE(SUM(l.credit), 0) as credit",
#             'foreign_balance': "(SELECT CASE WHEN currency_id IS NULL THEN 0 ELSE COALESCE(SUM(l.amount_currency), 0) END FROM account_account WHERE id IN (l.account_id)) as foreign_balance",
#         }
#         
#         children_and_consolidated = self._get_children_and_consol(cr, uid, ids, context=context)
#         accounts = {}
#         res = {}
#         null_result = dict((fn, 0.0) for fn in field_names)
#         if children_and_consolidated:
#             wheres = [""]
#             if query.strip():
#                 wheres.append(query.strip())
#             filters = " AND ".join(wheres)
# 
#             request = ("SELECT l.account_id as id, " +\
#                        ', '.join(mapping.values()) +
#                        " FROM account_move_line l" \
#                        " WHERE l.account_id IN %s " \
#                             + filters +
#                        " GROUP BY l.account_id")
#             params = (tuple(children_and_consolidated),) + query_params
#             cr.execute(request, params)
# 
#             for row in cr.dictfetchall():
#                 accounts[row['id']] = row
# 
# 
#             children_and_consolidated.reverse()
#             brs = list(self.browse(cr, uid, children_and_consolidated, context=context))
#             sums = {}
#             currency_obj = self.pool.get('res.currency')
#             while brs:
#                 current = brs.pop(0)
#                 for fn in field_names:
#                     sums.setdefault(current.id, {})[fn] = accounts.get(current.id, {}).get(fn, 0.0)
#                     for child in current.child_id:
#                         if child.company_id.currency_id.id == current.company_id.currency_id.id:
#                             sums[current.id][fn] += sums[child.id][fn]
#                         else:
#                             sums[current.id][fn] += currency_obj.compute(cr, uid, child.company_id.currency_id.id, current.company_id.currency_id.id, sums[child.id][fn], context=context)
# 
#                 if current.currency_id and current.exchange_rate and \
#                             ('adjusted_balance' in field_names or 'unrealized_gain_loss' in field_names):
# 
#                     adj_bal = sums[current.id].get('foreign_balance', 0.0) / current.exchange_rate
#                     sums[current.id].update({'adjusted_balance': adj_bal, 'unrealized_gain_loss': adj_bal - sums[current.id].get('balance', 0.0)})
# 
#             for id in ids:
#                 res[id] = sums.get(id, null_result)
#         else:
#             for id in ids:
#                 res[id] = null_result
#         return res
# 
#     def _set_credit_debit(self, cr, uid, account_id, name, value, arg, context=None):
#         if context.get('config_invisible', True):
#             return True
#         account = self.browse(cr, uid, account_id, context=context)
#         diff = value - getattr(account,name)
#         if not diff:
#             return True
# 
#         journal_obj = self.pool.get('account.journal')
#         jids = journal_obj.search(cr, uid, [('type','=','situation'),('centralisation','=',1),('company_id','=',account.company_id.id)], context=context)
#         if not jids:
#             raise osv.except_osv(_('Error!'),_("You need an Opening journal with centralisation checked to set the initial balance."))
# 
#         period_obj = self.pool.get('account.period')
#         pids = period_obj.search(cr, uid, [('special','=',True),('company_id','=',account.company_id.id)], context=context)
#         if not pids:
#             raise osv.except_osv(_('Error!'),_("There is no opening/closing period defined, please create one to set the initial balance."))
# 
#         move_obj = self.pool.get('account.move.line')
#         move_id = move_obj.search(cr, uid, [('journal_id','=',jids[0]), ('period_id','=',pids[0]), ('account_id','=', account_id), (name,'>', 0.0), ('name','=', _('Opening Balance'))], context=context)
#         if move_id:
#             move = move_obj.browse(cr, uid, move_id[0], context=context)
#             move_obj.write(cr, uid, move_id[0], {name: diff+getattr(move,name)}, context=context)
#         else:
#             if diff<0.0:
#                 raise osv.except_osv(_('Error!'),_("Unable to adapt the initial balance (negative value)."))
#             nameinv = (name=='credit' and 'debit') or 'credit'
#             move_id = move_obj.create(cr, uid, {'name': _('Opening Balance'),
#                 'account_id': account_id, 'journal_id': jids[0], 'period_id': pids[0],
#                 name: diff,
#                 nameinv: 0.0
#             }, context=context)
#         return True

#                 'balance': fields.function(__compute, digits_compute=dp.get_precision('Account'), string='Balance', multi='balance'),
#                 'credit': fields.function(__compute, fnct_inv=_set_credit_debit, digits_compute=dp.get_precision('Account'), string='Credit', multi='balance'),
#                 'debit': fields.function(__compute, fnct_inv=_set_credit_debit, digits_compute=dp.get_precision('Account'), string='Debit', multi='balance'),
#                 'foreign_balance': fields.function(__compute, digits_compute=dp.get_precision('Account'), string='Foreign Balance', multi='balance', help="Total amount (in Secondary currency) for transactions held in secondary currency for this account."),
#                 'adjusted_balance': fields.function(__compute, digits_compute=dp.get_precision('Account'), string='Adjusted Balance', multi='balance', help="Total amount (in Company currency) for transactions held in secondary currency for this account."),
#                 'unrealized_gain_loss': fields.function(__compute, digits_compute=dp.get_precision('Account'), string='Unrealized Gain or Loss', multi='balance', help="Value of Loss or Gain due to changes in exchange rate when doing multi-currency transactions."),
