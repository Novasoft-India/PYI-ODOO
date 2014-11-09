from openerp.osv import osv
from openerp.osv import fields

class opportunity_2slip(osv.osv):

    _name = 'opportunity.2slip'
    _description = 'opportunity.2slip'
    _inherit = 'crm.lead2opportunity.partner' 
    
 
    _columns = {
            'name': fields.selection([
                ('convert', 'Convert to slip'),
                ('merge', 'Merge with existing slip')
            ], 'Conversion Action', required=True),
        }
opportunity_2slip()