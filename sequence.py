from openerp.osv import orm, fields
from openerp.tools.translate import _


class sequence_insurance(orm.Model):
    _inherit = 'res.partner'
    
    def create(self, cr, uid, vals, context=None):
        vals['default_code'] = self.pool.get('ir.sequence').get(cr, uid, 'RES')
        new_id = super(sequence_insurance, self).create(cr, uid, vals, context=context)
        partner = self.browse(cr, uid, new_id, context=context)
        self._fields_sync(cr, uid, partner, vals, context)
        self._handle_first_contact_creation(cr, uid, partner, context)
        return new_id

    _columns = {
        'default_code': fields.char('Client No:',
                                    size=64)   
                    }

    _sql_constraints = [
        ('uniq_default_code',
         'unique(default_code)',
         'The reference must be unique'),
    ]
sequence_insurance()