from openerp.osv import osv
from openerp.osv import fields

class account_analytic_account(osv.osv):
 
    _inherit='account.analytic.account'
    
    _columns = {
             'policy_an':fields.char('Policy No:', size=128, required=False),
             'policy_type_an':fields.many2one('product.template','Select Policy',ondelete="set null"),
             
             #'assesment_head_id':fields.many2one('wakf.assesment.head','Head',ondelete="set null"),
             #'expense_id':fields.one2many('wakf.assesment.expense','assesment_id','Incomes'),
        }
account_analytic_account()
