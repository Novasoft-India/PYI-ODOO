from openerp.osv import osv
from openerp.osv import fields
import openerp.tools
from openerp.tools.translate import _
from openerp.exceptions import except_orm, Warning, RedirectWarning

class account_invoice1(osv.osv):
    _inherit='account.invoice'
    
    def product_id_change(self, product, uom_id, qty=0, name='', type='out_invoice',partner_id=False, fposition_id=False, price_unit=False, currency_id=False,company_id=None):
        context = self._context
        company_id = company_id if company_id is not None else context.get('company_id', False)
        self = self.with_context(company_id=company_id, force_company=company_id)
        if not partner_id:
            raise except_orm(_('No Partner Defined!'), _("You must first select a partner!"))
        if not product:
            if type in ('in_invoice', 'in_refund'):
                return {'value': {}, 'domain': {'product_uom': []}}
            else:
                return {'value': {'price_unit': 0.0}, 'domain': {'product_uom': []}}

        values = {}

        part = self.env['res.partner'].browse(partner_id)
        fpos = self.env['account.fiscal.position'].browse(fposition_id)

        if part.lang:
            self = self.with_context(lang=part.lang)
        product = self.env['product.product'].browse(product)

        values['name'] = product.partner_ref
        if type in ('out_invoice', 'out_refund'):
            account = product.property_account_income or product.categ_id.property_account_income_categ
        else:
            account = product.property_account_expense or product.categ_id.property_account_expense_categ
        account = fpos.map_account(account)
        if account:
            values['account_id'] = account.id

        if type in ('out_invoice', 'out_refund'):
            taxes = product.taxes_id or account.tax_ids
            if product.description_sale:
                values['name'] += '\n' + product.description_sale
        else:
            taxes = product.supplier_taxes_id or account.tax_ids
            if product.description_purchase:
                values['name'] += '\n' + product.description_purchase

        taxes = fpos.map_tax(taxes)
        values['invoice_line_tax_id'] = taxes.ids

        if type in ('in_invoice', 'in_refund'):
            values['price_unit'] = price_unit or product.standard_price
        else:
            values['price_unit'] = product.list_price

        values['uos_id'] = uom_id or product.uom_id.id
        domain = {'uos_id': [('category_id', '=', product.uom_id.category_id.id)]}

        company = self.env['res.company'].browse(company_id)
        currency = self.env['res.currency'].browse(currency_id)

        if company and currency:
            if company.currency_id != currency:
                if type in ('in_invoice', 'in_refund'):
                    values['price_unit'] = product.standard_price
                values['price_unit'] = values['price_unit'] * currency.rate

            if values['uos_id'] and values['uos_id'] != product.uom_id.id:
                values['price_unit'] = self.env['product.uom']._compute_price(
                    product.uom_id.id, values['price_unit'], values['uos_id'])

        return {'value': values, 'domain': domain}
    
account_invoice1()
    

class account_invoice_line(osv.osv):

    _inherit='account.invoice.line'
    
    
        
    _columns = {
            'insured_amt_acc_inline':fields.float('Insured', size=64, required=False, readonly=False),          
            'period_insured_acc_inline':fields.date('Period Insured',required=False,size=32),          
            'premium_acc_inline':fields.float('Premium',size=64, required=False, readonly=False),
            'deduct_acc_inline':fields.float('Deductable',size=64, required=False, readonly=False),
            'com_acc_inline':fields.float('Commission', size=64, required=False, readonly=False),
            'agent_acc_inline':fields.float('Agent Commission', size=64, required=False, readonly=False),
            'pass_value_p2acc_inline':fields.char('Value Pass', size=64, required=False, readonly=False),
            #
            'Vehicle_quote_acc_inline':fields.char('Insured Vehicle', size=128, required=False), 
            'situation_quo_acc_inline':fields.text('Situation',size=64,required=False),
            'limit_los_quo_acc_inline':fields.integer('Loss limit',size=64,required=False),
            'car_quote_acc_inline':fields.char('Cargo', size=128, required=False),
            'des_quote_acc_inline':fields.char('Destination', size=128, required=False),
            'plan_quote_acc_inline':fields.char('Name Of Plan', size=128, required=False),
            'xcess_quote_acc_inline':fields.integer('Excess',size=64,required=False),
            'work_quote_acc_inline':fields.text('Scope Of Work', size=128, required=False),
            'bov_quote_acc_inline':fields.integer('B.O.V',size=64,required=False),
            # Additional Datas
            'sum_insur_qu_acc_inline':fields.float('Sum insured', size=64, required=False, readonly=False),
            'sum_insur_qu_acc_inline1':fields.float('Sum insured', size=64, required=False, readonly=False),
            'sum_insur_qu_acc_inline2':fields.float('Sum insured', size=64, required=False, readonly=False),
            'sum_insur_qu_acc_inline3':fields.float('Sum insured', size=64, required=False, readonly=False),
            'sum_insur_qu_acc_inline4':fields.float('Sum insured', size=64, required=False, readonly=False),
            'sum_insur_qu_acc_inline5':fields.float('Sum insured', size=64, required=False, readonly=False),
            'sum_insur_qu_acc_inline6':fields.float('Sum insured', size=64, required=False, readonly=False),
            'sum_insur_qu_acc_inline7':fields.float('Sum insured', size=64, required=False, readonly=False),
            'sum_insur_qu_acc_inline8':fields.float('Sum insured', size=64, required=False, readonly=False),
            'sum_insur_qu_acc_inline9':fields.float('Sum insured', size=64, required=False, readonly=False),
            'sum_insur_qu_acc_inline10':fields.float('Sum insured', size=64, required=False, readonly=False),
            'sum_insur_qu_acc_inline11':fields.float('Sum insured', size=64, required=False, readonly=False),
            'sum_insur_qu_acc_inline12':fields.float('Sum insured', size=64, required=False, readonly=False),
            'sum_insur_qu_acc_inline13':fields.float('Sum insured', size=64, required=False, readonly=False),
            'sum_insur_qu_acc_inline14':fields.float('Sum insured', size=64, required=False, readonly=False),
            'sum_insur_qu_acc_inline15':fields.float('Sum insured', size=64, required=False, readonly=False),
            'sum_insur_qu_acc_inline16':fields.float('Sum insured', size=64, required=False, readonly=False),
            'sum_insur_qu_acc_inline17':fields.float('Sum insured', size=64, required=False, readonly=False),
            'sum_insur_qu_acc_inline18':fields.float('Sum insured', size=64, required=False, readonly=False),
            'sum_insur_qu_acc_inline19':fields.float('Sum insured', size=64, required=False, readonly=False),
            'sum_insur_qu_acc_inline20':fields.float('Sum insured', size=64, required=False, readonly=False),
            'sum_insur_qu_acc_inline21':fields.float('Sum insured', size=64, required=False, readonly=False),
            'sum_insur_qu_acc_inline22':fields.float('Sum insured', size=64, required=False, readonly=False),
            'sum_insur_qu_acc_inline23':fields.float('Sum insured', size=64, required=False, readonly=False),
            'period_quote_acc_inline':fields.text('Cancelation Period Conditions',size=64,required=False),
            'period_quote_acc_inline1':fields.text('Cancelation Period Conditions',size=64,required=False),                
            'busines_quote_acc_inline':fields.char('Insured business', size=128, required=False),
            'busines_quote_acc_inline1':fields.char('Insured business', size=128, required=False),
            'person_quote_acc_inline':fields.integer('Insured Persons',size=64,required=False),
            'person_quote_acc_inline1':fields.integer('Insured Persons',size=64,required=False),
            'ocupancy_quo_acc_inline':fields.integer('Occupancy',size=64,required=False),
            'ocupancy_quo_acc_inline1':fields.integer('Occupancy',size=64,required=False),
            'ocupancy_quo_acc_inline2':fields.integer('Occupancy',size=64,required=False),
            'ocupancy_quo_acc_inline3':fields.integer('Occupancy',size=64,required=False),
            'ocupancy_quo_acc_inline4':fields.integer('Occupancy',size=64,required=False),
            'ocupancy_quo_acc_inline5':fields.integer('Occupancy',size=64,required=False),
            'ocupancy_quo_acc_inline6':fields.integer('Occupancy',size=64,required=False),
            'ocupancy_quo_acc_inline7':fields.integer('Occupancy',size=64,required=False),
            'ocupancy_quo_acc_inline8':fields.integer('Occupancy',size=64,required=False),
            'ocupancy_quo_acc_inline9':fields.integer('Occupancy',size=64,required=False),
            'ocupancy_quo_acc_inline10':fields.integer('Occupancy',size=64,required=False),
            'ocupancy_quo_acc_inline11':fields.integer('Occupancy',size=64,required=False),
            'ocupancy_quo_acc_inline12':fields.integer('Occupancy',size=64,required=False), 
            'voyage_quote_acc_inline':fields.char('Voyage', size=128, required=False),
            'voyage_quote_acc_inline1':fields.char('Voyage', size=128, required=False),                
            'limit_quote_acc_inline':fields.integer('Limit',size=64,required=False),
            'limit_quote_acc_inline1':fields.integer('Limit',size=64,required=False),
            'limit_quote_acc_inline2':fields.integer('Limit',size=64,required=False),
            'name_quote_acc_inline':fields.char('Cover Name', size=128, required=False),
            'name_quote_acc_inline1':fields.char('Cover Name', size=128, required=False),
            'name_quote_acc_inline2':fields.char('Cover Name', size=128, required=False),     
            'liability_quo_acc_inline':fields.integer('Limit Of Liability',size=64,required=False),
            'liability_quo_acc_inline1':fields.integer('Limit Of Liability',size=64,required=False),
            'xtensions_quo_acc_inline':fields.date('Extensions',required=False,size=32),
            'xtensions_quo_acc_inline1':fields.date('Extensions',required=False,size=32),
            'xtensions_quo_acc_inline2':fields.date('Extensions',required=False,size=32),
            'xtensions_quo_acc_inline3':fields.date('Extensions',required=False,size=32),
            'benefit_quo_acc_inline':fields.char('Benefits covered', size=128, required=False),
            'benefit_quo_acc_inline1':fields.char('Benefits covered', size=128, required=False),
            'benefit_quo_acc_inline2':fields.char('Benefits covered', size=128, required=False),
            'benefit_quo_acc_inline3':fields.char('Benefits covered', size=128, required=False),
            'benefit_quo_acc_inline4':fields.char('Benefits covered', size=128, required=False),
            'benefit_quo_acc_inline5':fields.char('Benefits covered', size=128, required=False),
            'benefit_quo_acc_inline6':fields.char('Benefits covered', size=128, required=False),
            'benefit_quo_acc_inline7':fields.char('Benefits covered', size=128, required=False),
            'benefit_quo_acc_inline8':fields.char('Benefits covered', size=128, required=False),
            'benefit_quo_acc_inline9':fields.char('Benefits covered', size=128, required=False),
            'benefit_quo_acc_inline10':fields.char('Benefits covered', size=128, required=False),
            'benefit_quo_acc_inline11':fields.char('Benefits covered', size=128, required=False),
            'benefit_quo_acc_inline12':fields.char('Benefits covered', size=128, required=False),
            'benefit_quo_acc_inline13':fields.char('Benefits covered', size=128, required=False),
            'benefit_quo_acc_inline14':fields.char('Benefits covered', size=128, required=False),
            'benefit_quo_acc_inline15':fields.char('Benefits covered', size=128, required=False),
            'benefit_quo_acc_inline16':fields.char('Benefits covered', size=128, required=False),
            'benefit_quo_acc_inline17':fields.char('Benefits covered', size=128, required=False),
            'benefit_quo_acc_inline18':fields.char('Benefits covered', size=128, required=False),
            'benefit_quo_acc_inline19':fields.char('Benefits covered', size=128, required=False),
            'benefit_quo_acc_inline20':fields.char('Benefits covered', size=128, required=False),
            'benefit_quo_acc_inline21':fields.char('Benefits covered', size=128, required=False),
            'benefit_quo_acc_inline22':fields.char('Benefits covered', size=128, required=False),
            'rate_quote_acc_inline':fields.float('Rate', size=64, required=False, readonly=False),
            'rate_quote_acc_inline1':fields.float('Rate', size=64, required=False, readonly=False),
        }
account_invoice_line()