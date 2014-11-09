from openerp.osv import osv
from openerp.osv import fields

class crm_helpdesk(osv.osv):

    _inherit='crm.helpdesk'
    
    _columns = {
            'policy1':fields.integer('Policy No:', size=64, required=False, readonly=False),
            'policy2':fields.char('Policy Type', size=64, required=False, readonly=False),
            }
crm_helpdesk()