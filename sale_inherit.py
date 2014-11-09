from openerp.osv import osv
from openerp.osv import fields
import openerp.tools
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare
import time
from datetime import datetime
from datetime import date,timedelta
from dateutil.relativedelta import relativedelta
from openerp import netsvc

class sale_order(osv.osv):

    _inherit='sale.order'
    
    _columns = {
            'date_quote_sale_order':fields.date('Date Quote Delivered',required=True,size=32),
            'quote_valide_sale_order':fields.date('Quote Valid for',required=True,size=32),
            #############################################################################################
            'type_sale_order':fields.char('Type', size=64, required=False, readonly=False), 
            'stage_sale_order':fields.char('Stage', size=64, required=False, readonly=False),
            'details_sale_order': fields.text('Details'),
            'docs_sale_order': fields.many2one('ir.attachment', 'Doucuments'),   
        }
sale_order()

class sale_order_line(osv.osv):

    _inherit='sale.order.line'
    
    def _prepare_order_line_invoice_line(self, cr, uid, line, account_id=False, context=None):
        """Prepare the dict of values to create the new invoice line for a
           sales order line. This method may be overridden to implement custom
           invoice generation (making sure to call super() to establish
           a clean extension chain).

           :param browse_record line: sale.order.line record to invoice
           :param int account_id: optional ID of a G/L account to force
               (this is used for returning products including service)
           :return: dict of values to create() the invoice line
        """
        res = {}
        if not line.invoiced:
            if not account_id:
                if line.product_id:
                    account_id = line.product_id.property_account_income.id
                    if not account_id:
                        account_id = line.product_id.categ_id.property_account_income_categ.id
                    if not account_id:
                        raise osv.except_osv(_('Error!'),
                                _('Please define income account for this product: "%s" (id:%d).') % \
                                    (line.product_id.name, line.product_id.id,))
                else:
                    prop = self.pool.get('ir.property').get(cr, uid,
                            'property_account_income_categ', 'product.category',
                            context=context)
                    account_id = prop and prop.id or False
            uosqty = self._get_line_qty(cr, uid, line, context=context)
            uos_id = self._get_line_uom(cr, uid, line, context=context)
            pu = 0.0
            if uosqty:
                pu = round(line.price_unit * line.product_uom_qty / uosqty,
                        self.pool.get('decimal.precision').precision_get(cr, uid, 'Product Price'))
            fpos = line.order_id.fiscal_position or False
            account_id = self.pool.get('account.fiscal.position').map_account(cr, uid, fpos, account_id)
            if not account_id:
                raise osv.except_osv(_('Error!'),
                            _('There is no Fiscal Position defined or Income category account defined for default properties of Product categories.'))
            res = {
                'name': line.name,
                'sequence': line.sequence,
                'origin': line.order_id.name,
                'account_id': account_id,
                'price_unit': pu,
                'quantity': uosqty,
                'discount': line.discount,
                'uos_id': uos_id,
                'product_id': line.product_id.id or False,
                'invoice_line_tax_id': [(6, 0, [x.id for x in line.tax_id])],
                'account_analytic_id': line.order_id.project_id and line.order_id.project_id.id or False,
                'insured_amt_acc_inline':line.insured_amt,
                'premium_acc_inline':line.ppremium,
                'deduct_acc_inline':line.deduct,
                'com_acc_inline':line.ccom
            }

        return res
    
    
    def invoice_line_create(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        create_ids = []
        sales = set()
        for line in self.browse(cr, uid, ids, context=context):
            vals = self._prepare_order_line_invoice_line(cr, uid, line, False, context)
            if vals:
                inv_id = self.pool.get('account.invoice.line').create(cr, uid, vals, context=context)
                self.write(cr, uid, [line.id], {'invoice_lines': [(4, inv_id)]}, context=context)
                sales.add(line.order_id.id)
                create_ids.append(inv_id)
        # Trigger workflow events
        wf_service = netsvc.LocalService("workflow")
        for sale_id in sales:
            wf_service.trg_write(uid, 'sale.order', sale_id, cr)
        return create_ids
    
    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context=None):
        context = context or {}
        lang = lang or context.get('lang',False)
        if not  partner_id:
            raise osv.except_osv(_('No Customer Defined!'), _('Before choosing a product,\n select a customer in the sales form.'))
        warning = {}
        product_uom_obj = self.pool.get('product.uom')
        partner_obj = self.pool.get('res.partner')
        product_obj = self.pool.get('product.product')
        context = {'lang': lang, 'partner_id': partner_id}
        if partner_id:
            lang = partner_obj.browse(cr, uid, partner_id).lang
        context_partner = {'lang': lang, 'partner_id': partner_id}
        
        if product:
            insured_amt_val =self.pool.get('product.template').browse(cr,uid,product).insured_amt_product 
            premium_val =self.pool.get('product.template').browse(cr,uid,product).premium_cost_product  
            deductable_val =self.pool.get('product.template').browse(cr,uid,product).deductable_product
            period_insured_val =self.pool.get('product.template').browse(cr,uid,product).period_insured_product
            commission_val = self.pool.get('product.template').browse(cr,uid,product).com_product
            agent_val = self.pool.get('product.template').browse(cr,uid,product).agent_product
            ###################################################################################
            Vehicle_quote_val = self.pool.get('product.template').browse(cr,uid,product).Vehicle_quote_product
            situation_quote_val = self.pool.get('product.template').browse(cr,uid,product).situation_quote_product
            limit_los_quote_val = self.pool.get('product.template').browse(cr,uid,product).limit_los_quote_product
            car_quote_val = self.pool.get('product.template').browse(cr,uid,product).car_quote_product
            des_quote_val = self.pool.get('product.template').browse(cr,uid,product).des_quote_product
            plan_quote_val = self.pool.get('product.template').browse(cr,uid,product).plan_quote_product
            xcess_quote_val = self.pool.get('product.template').browse(cr,uid,product).xcess_quote_product
            work_quote_val = self.pool.get('product.template').browse(cr,uid,product).work_quote_product
            bov_quote_val = self.pool.get('product.template').browse(cr,uid,product).bov_quote_product
            ###################################################################################
            sum_insured_quote_product_val = self.pool.get('product.template').browse(cr,uid,product).sum_insured_quote_product
            sum_insured_quote_product1_val = self.pool.get('product.template').browse(cr,uid,product).sum_insured_quote_product1
            sum_insured_quote_product2_val = self.pool.get('product.template').browse(cr,uid,product).sum_insured_quote_product2
            sum_insured_quote_product3_val = self.pool.get('product.template').browse(cr,uid,product).sum_insured_quote_product3
            sum_insured_quote_product4_val = self.pool.get('product.template').browse(cr,uid,product).sum_insured_quote_product4
            sum_insured_quote_product5_val = self.pool.get('product.template').browse(cr,uid,product).sum_insured_quote_product5
            sum_insured_quote_product6_val = self.pool.get('product.template').browse(cr,uid,product).sum_insured_quote_product6
            sum_insured_quote_product7_val = self.pool.get('product.template').browse(cr,uid,product).sum_insured_quote_product7
            sum_insured_quote_product8_val = self.pool.get('product.template').browse(cr,uid,product).sum_insured_quote_product8
            sum_insured_quote_product9_val = self.pool.get('product.template').browse(cr,uid,product).sum_insured_quote_product9
            sum_insured_quote_product10_val = self.pool.get('product.template').browse(cr,uid,product).sum_insured_quote_product10
            sum_insured_quote_product11_val = self.pool.get('product.template').browse(cr,uid,product).sum_insured_quote_product11
            sum_insured_quote_product12_val = self.pool.get('product.template').browse(cr,uid,product).sum_insured_quote_product12
            sum_insured_quote_product13_val = self.pool.get('product.template').browse(cr,uid,product).sum_insured_quote_product13
            sum_insured_quote_product14_val = self.pool.get('product.template').browse(cr,uid,product).sum_insured_quote_product14
            sum_insured_quote_product15_val = self.pool.get('product.template').browse(cr,uid,product).sum_insured_quote_product15
            sum_insured_quote_product16_val = self.pool.get('product.template').browse(cr,uid,product).sum_insured_quote_product16
            sum_insured_quote_product17_val = self.pool.get('product.template').browse(cr,uid,product).sum_insured_quote_product17
            sum_insured_quote_product18_val = self.pool.get('product.template').browse(cr,uid,product).sum_insured_quote_product18
            sum_insured_quote_product19_val = self.pool.get('product.template').browse(cr,uid,product).sum_insured_quote_product19
            sum_insured_quote_product20_val = self.pool.get('product.template').browse(cr,uid,product).sum_insured_quote_product20
            sum_insured_quote_product21_val = self.pool.get('product.template').browse(cr,uid,product).sum_insured_quote_product21
            sum_insured_quote_product22_val = self.pool.get('product.template').browse(cr,uid,product).sum_insured_quote_product22
            sum_insured_quote_product23_val = self.pool.get('product.template').browse(cr,uid,product).sum_insured_quote_product23
            period_quote_val = self.pool.get('product.template').browse(cr,uid,product).period_quote_product
            period_quote1_val = self.pool.get('product.template').browse(cr,uid,product).period_quote_product1
            busines_quote_val = self.pool.get('product.template').browse(cr,uid,product).busines_quote_product
            busines_quote1_val = self.pool.get('product.template').browse(cr,uid,product).busines_quote_product1
            person_quote_val = self.pool.get('product.template').browse(cr,uid,product).person_quote_product
            person_quote1_val = self.pool.get('product.template').browse(cr,uid,product).person_quote_product1
            ocupancy_quote_val = self.pool.get('product.template').browse(cr,uid,product).ocupancy_quote_product
            ocupancy_quote1_val = self.pool.get('product.template').browse(cr,uid,product).ocupancy_quote_product1
            ocupancy_quote2_val = self.pool.get('product.template').browse(cr,uid,product).ocupancy_quote_product2
            ocupancy_quote3_val = self.pool.get('product.template').browse(cr,uid,product).ocupancy_quote_product3
            ocupancy_quote4_val = self.pool.get('product.template').browse(cr,uid,product).ocupancy_quote_product4
            ocupancy_quote5_val = self.pool.get('product.template').browse(cr,uid,product).ocupancy_quote_product5
            ocupancy_quote6_val = self.pool.get('product.template').browse(cr,uid,product).ocupancy_quote_product6
            ocupancy_quote7_val = self.pool.get('product.template').browse(cr,uid,product).ocupancy_quote_product7
            ocupancy_quote8_val = self.pool.get('product.template').browse(cr,uid,product).ocupancy_quote_product8
            ocupancy_quote9_val = self.pool.get('product.template').browse(cr,uid,product).ocupancy_quote_product9
            ocupancy_quote10_val = self.pool.get('product.template').browse(cr,uid,product).ocupancy_quote_product10
            ocupancy_quote11_val = self.pool.get('product.template').browse(cr,uid,product).ocupancy_quote_product11
            ocupancy_quote12_val = self.pool.get('product.template').browse(cr,uid,product).ocupancy_quote_product12
            voyage_quote_val = self.pool.get('product.template').browse(cr,uid,product).voyage_quote_product
            voyage_quote1_val = self.pool.get('product.template').browse(cr,uid,product).voyage_quote_product1
            limit_quote_val = self.pool.get('product.template').browse(cr,uid,product).limit_quote_product
            limit_quote1_val = self.pool.get('product.template').browse(cr,uid,product).limit_quote_product1
            limit_quote2_val = self.pool.get('product.template').browse(cr,uid,product).limit_quote_product2
            name_quote_val = self.pool.get('product.template').browse(cr,uid,product).name_quote_product
            name_quote1_val = self.pool.get('product.template').browse(cr,uid,product).name_quote_product1
            name_quote2_val = self.pool.get('product.template').browse(cr,uid,product).name_quote_product2
            liability_quote_val = self.pool.get('product.template').browse(cr,uid,product).liability_quote_product
            liability_quote1_val = self.pool.get('product.template').browse(cr,uid,product).liability_quote_product1
            xtensions_quote_val = self.pool.get('product.template').browse(cr,uid,product).xtensions_quote_product
            xtensions_quote1_val = self.pool.get('product.template').browse(cr,uid,product).xtensions_quote_product1
            xtensions_quote2_val = self.pool.get('product.template').browse(cr,uid,product).xtensions_quote_product2
            xtensions_quote3_val = self.pool.get('product.template').browse(cr,uid,product).xtensions_quote_product3
            benefit_quote_val = self.pool.get('product.template').browse(cr,uid,product).benefit_quote_product
            benefit_quote1_val = self.pool.get('product.template').browse(cr,uid,product).benefit_quote_product1
            benefit_quote2_val = self.pool.get('product.template').browse(cr,uid,product).benefit_quote_product2
            benefit_quote3_val = self.pool.get('product.template').browse(cr,uid,product).benefit_quote_product3
            benefit_quote4_val = self.pool.get('product.template').browse(cr,uid,product).benefit_quote_product4
            benefit_quote5_val = self.pool.get('product.template').browse(cr,uid,product).benefit_quote_product5
            benefit_quote6_val = self.pool.get('product.template').browse(cr,uid,product).benefit_quote_product6
            benefit_quote7_val = self.pool.get('product.template').browse(cr,uid,product).benefit_quote_product7
            benefit_quote8_val = self.pool.get('product.template').browse(cr,uid,product).benefit_quote_product8
            benefit_quote9_val = self.pool.get('product.template').browse(cr,uid,product).benefit_quote_product9
            benefit_quote10_val = self.pool.get('product.template').browse(cr,uid,product).benefit_quote_product10
            benefit_quote11_val = self.pool.get('product.template').browse(cr,uid,product).benefit_quote_product11
            benefit_quote12_val = self.pool.get('product.template').browse(cr,uid,product).benefit_quote_product12
            benefit_quote13_val = self.pool.get('product.template').browse(cr,uid,product).benefit_quote_product13
            benefit_quote14_val = self.pool.get('product.template').browse(cr,uid,product).benefit_quote_product14
            benefit_quote15_val = self.pool.get('product.template').browse(cr,uid,product).benefit_quote_product15
            benefit_quote16_val = self.pool.get('product.template').browse(cr,uid,product).benefit_quote_product16
            benefit_quote17_val = self.pool.get('product.template').browse(cr,uid,product).benefit_quote_product17
            benefit_quote18_val = self.pool.get('product.template').browse(cr,uid,product).benefit_quote_product18
            benefit_quote19_val = self.pool.get('product.template').browse(cr,uid,product).benefit_quote_product19
            benefit_quote20_val = self.pool.get('product.template').browse(cr,uid,product).benefit_quote_product20
            benefit_quote21_val = self.pool.get('product.template').browse(cr,uid,product).benefit_quote_product21
            benefit_quote22_val = self.pool.get('product.template').browse(cr,uid,product).benefit_quote_product22
            rate_quote_val = self.pool.get('product.template').browse(cr,uid,product).rate_quote_product
            rate_quote1_val = self.pool.get('product.template').browse(cr,uid,product).rate_quote_product1
                   
        if not product:
            return {'value': {'th_weight': 0,
                'product_uos_qty': qty}, 'domain': {'product_uom': [],
                   'product_uos': []}}
        if not date_order:
            date_order = time.strftime(DEFAULT_SERVER_DATE_FORMAT)

        result = {}
        warning_msgs = ''
        product_obj = product_obj.browse(cr, uid, product, context=context_partner)
        name_id=self.pool.get('product.product').browse(cr, uid, product).name
        result['work_quote'] = name_id
        result['insured_amt'] = insured_amt_val
        result['ppremium'] = premium_val
        result['deduct'] = deductable_val
        result['pperiod_insured'] = period_insured_val
        result['ccom'] = commission_val
        result['aagent'] = agent_val
        ###########################################
        result['Vehicle_quote'] = Vehicle_quote_val
        result['situation_quote'] = situation_quote_val
        result['limit_los_quote'] = limit_los_quote_val
        result['car_quote'] = car_quote_val
        result['des_quote'] = des_quote_val
        result['plan_quote'] = plan_quote_val
        result['xcess_quote'] = xcess_quote_val
        result['work_quote_so_line'] = work_quote_val
        result['bov_quote'] = bov_quote_val
        ###########################################
        result['sum_insured_quote'] = sum_insured_quote_product_val
        result['sum_insured_quote1'] = sum_insured_quote_product1_val
        result['sum_insured_quote2'] = sum_insured_quote_product2_val
        result['sum_insured_quote3'] = sum_insured_quote_product3_val
        result['sum_insured_quote4'] = sum_insured_quote_product4_val
        result['sum_insured_quote5'] = sum_insured_quote_product5_val
        result['sum_insured_quote6'] = sum_insured_quote_product6_val
        result['sum_insured_quote7'] = sum_insured_quote_product7_val
        result['sum_insured_quote8'] = sum_insured_quote_product8_val
        result['sum_insured_quote9'] = sum_insured_quote_product9_val
        result['sum_insured_quote10'] = sum_insured_quote_product10_val
        result['sum_insured_quote11'] = sum_insured_quote_product11_val
        result['sum_insured_quote12'] = sum_insured_quote_product12_val
        result['sum_insured_quote13'] = sum_insured_quote_product13_val
        result['sum_insured_quote14'] = sum_insured_quote_product14_val
        result['sum_insured_quote15'] = sum_insured_quote_product15_val
        result['sum_insured_quote16'] = sum_insured_quote_product16_val
        result['sum_insured_quote17'] = sum_insured_quote_product17_val
        result['sum_insured_quote18'] = sum_insured_quote_product18_val
        result['sum_insured_quote19'] = sum_insured_quote_product19_val
        result['sum_insured_quote20'] = sum_insured_quote_product20_val
        result['sum_insured_quote21'] = sum_insured_quote_product21_val
        result['sum_insured_quote22'] = sum_insured_quote_product22_val
        result['sum_insured_quote23'] = sum_insured_quote_product23_val
        result['period_quote'] = period_quote_val
        result['period_quote1'] = period_quote1_val
        result['busines_quote'] = busines_quote_val
        result['busines_quote1'] = busines_quote1_val
        result['person_quote'] = person_quote_val
        result['person_quote1'] = person_quote1_val
        result['ocupancy_quote'] = ocupancy_quote_val
        result['ocupancy_quote1'] = ocupancy_quote1_val
        result['ocupancy_quote2'] = ocupancy_quote2_val
        result['ocupancy_quote3'] = ocupancy_quote3_val
        result['ocupancy_quote4'] = ocupancy_quote4_val
        result['ocupancy_quote5'] = ocupancy_quote5_val
        result['ocupancy_quote6'] = ocupancy_quote6_val
        result['ocupancy_quote7'] = ocupancy_quote7_val
        result['ocupancy_quote8'] = ocupancy_quote8_val
        result['ocupancy_quote9'] = ocupancy_quote9_val
        result['ocupancy_quote10'] = ocupancy_quote10_val
        result['ocupancy_quote11'] = ocupancy_quote11_val
        result['ocupancy_quote12'] = ocupancy_quote12_val
        result['voyage_quote'] = voyage_quote_val
        result['voyage_quote1'] = voyage_quote1_val
        result['limit_quote'] = limit_quote_val
        result['limit_quote1'] = limit_quote1_val
        result['limit_quote2'] = limit_quote2_val
        result['name_quote'] = name_quote_val
        result['name_quote1'] = name_quote1_val
        result['name_quote2'] = name_quote2_val
        result['liability_quote'] = liability_quote_val
        result['liability_quote1'] = liability_quote1_val
        result['xtensions_quote'] = xtensions_quote_val
        result['xtensions_quote1'] = xtensions_quote1_val
        result['xtensions_quote2'] = xtensions_quote2_val
        result['xtensions_quote3'] = xtensions_quote3_val
        result['benefit_quote'] = benefit_quote_val
        result['benefit_quote1'] = benefit_quote1_val
        result['benefit_quote2'] = benefit_quote2_val
        result['benefit_quote3'] = benefit_quote3_val
        result['benefit_quote4'] = benefit_quote4_val
        result['benefit_quote5'] = benefit_quote5_val
        result['benefit_quote6'] = benefit_quote6_val
        result['benefit_quote7'] = benefit_quote7_val
        result['benefit_quote8'] = benefit_quote8_val
        result['benefit_quote9'] = benefit_quote9_val
        result['benefit_quote10'] = benefit_quote10_val
        result['benefit_quote11'] = benefit_quote11_val
        result['benefit_quote12'] = benefit_quote12_val
        result['benefit_quote13'] = benefit_quote13_val
        result['benefit_quote14'] = benefit_quote14_val
        result['benefit_quote15'] = benefit_quote15_val
        result['benefit_quote16'] = benefit_quote16_val
        result['benefit_quote17'] = benefit_quote17_val
        result['benefit_quote18'] = benefit_quote18_val
        result['benefit_quote19'] = benefit_quote19_val
        result['benefit_quote20'] = benefit_quote20_val
        result['benefit_quote21'] = benefit_quote21_val
        result['benefit_quote22'] = benefit_quote22_val
        result['rate_quote'] = rate_quote_val
        result['rate_quote1'] = rate_quote1_val
        
        uom2 = False
        if uom:
            uom2 = product_uom_obj.browse(cr, uid, uom)
            if product_obj.uom_id.category_id.id != uom2.category_id.id:
                uom = False
        if uos:
            if product_obj.uos_id:
                uos2 = product_uom_obj.browse(cr, uid, uos)
                if product_obj.uos_id.category_id.id != uos2.category_id.id:
                    uos = False
            else:
                uos = False
        fpos = fiscal_position and self.pool.get('account.fiscal.position').browse(cr, uid, fiscal_position) or False
        if update_tax: #The quantity only have changed
            result['tax_id'] = self.pool.get('account.fiscal.position').map_tax(cr, uid, fpos, product_obj.taxes_id)

        if not flag:
            result['name'] = self.pool.get('product.product').name_get(cr, uid, [product_obj.id], context=context_partner)[0][1]
            if product_obj.description_sale:
                result['name'] += '\n'+product_obj.description_sale
        domain = {}
        if (not uom) and (not uos):
            result['product_uom'] = product_obj.uom_id.id
            if product_obj.uos_id:
                result['product_uos'] = product_obj.uos_id.id
                result['product_uos_qty'] = qty * product_obj.uos_coeff
                uos_category_id = product_obj.uos_id.category_id.id
            else:
                result['product_uos'] = False
                result['product_uos_qty'] = qty
                uos_category_id = False
            result['th_weight'] = qty * product_obj.weight
            domain = {'product_uom':
                        [('category_id', '=', product_obj.uom_id.category_id.id)],
                        'product_uos':
                        [('category_id', '=', uos_category_id)]}
        elif uos and not uom: # only happens if uom is False
            result['product_uom'] = product_obj.uom_id and product_obj.uom_id.id
            result['product_uom_qty'] = qty_uos / product_obj.uos_coeff
            result['th_weight'] = result['product_uom_qty'] * product_obj.weight
        elif uom: # whether uos is set or not
            default_uom = product_obj.uom_id and product_obj.uom_id.id
            q = product_uom_obj._compute_qty(cr, uid, uom, qty, default_uom)
            if product_obj.uos_id:
                result['product_uos'] = product_obj.uos_id.id
                result['product_uos_qty'] = qty * product_obj.uos_coeff
            else:
                result['product_uos'] = False
                result['product_uos_qty'] = qty
            result['th_weight'] = q * product_obj.weight        # Round the quantity up

        if not uom2:
            uom2 = product_obj.uom_id
        # get unit price

        if not pricelist:
            warn_msg = _('You have to select a pricelist or a customer in the sales form !\n'
                    'Please set one before choosing a product.')
            warning_msgs += _("No Pricelist ! : ") + warn_msg +"\n\n"
        else:
            price = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist],
                    product, qty or 1.0, partner_id, {
                        'uom': uom or result.get('product_uom'),
                        'date': date_order,
                        })[pricelist]
            if price is False:
                warn_msg = _("Cannot find a pricelist line matching this product and quantity.\n"
                        "You have to change either the product, the quantity or the pricelist.")

                warning_msgs += _("No valid pricelist line found ! :") + warn_msg +"\n\n"
            else:
                result.update({'price_unit': price})
        if warning_msgs:
            warning = {
                       'title': _('Configuration Error!'),
                       'message' : warning_msgs
                    }
        return {'value': result, 'domain': domain, 'warning': warning}
    
    _columns = {
            'product_product': fields.one2many('product.product', 'product_tmpl_id', 'Policy Type'),
            'insured_amt':fields.float('Insured Amount', size=64, required=False, readonly=False),          
            'pperiod_insured':fields.date('Period Insured',required=True,size=32),          
            'ppremium':fields.float('Premium',size=64, required=True, readonly=False),
            'deduct':fields.float('Deductable',size=64, required=True, readonly=False),
            'ccom':fields.float('Commission', size=64, required=False, readonly=False),
            'aagent':fields.float('Agent Commission', size=64, required=False, readonly=False),
            'work_quote':fields.char('Scope Of Work', size=128, required=False),
            #
            'Vehicle_quote':fields.char('Insured Vehicle', size=128, required=False), 
            'situation_quote':fields.text('Situation',size=64,required=False),
            'limit_los_quote':fields.integer('Loss limit',size=64,required=False),
            'car_quote':fields.char('Cargo', size=128, required=False),
            'des_quote':fields.char('Destination', size=128, required=False),
            'plan_quote':fields.char('Name Of Plan', size=128, required=False),
            'xcess_quote':fields.integer('Excess',size=64,required=False),
            'work_quote_so_line':fields.text('Scope Of Work', size=128, required=False),
            'bov_quote':fields.integer('B.O.V',size=64,required=False),
            # Additional Datas
            'sum_insured_quote':fields.float('Sum insured', size=64, required=False, readonly=False),
            'sum_insured_quote1':fields.float('Sum insured', size=64, required=False, readonly=False), 
            'sum_insured_quote2':fields.float('Sum insured', size=64, required=False, readonly=False), 
            'sum_insured_quote3':fields.float('Sum insured', size=64, required=False, readonly=False), 
            'sum_insured_quote4':fields.float('Sum insured', size=64, required=False, readonly=False), 
            'sum_insured_quote5':fields.float('Sum insured', size=64, required=False, readonly=False), 
            'sum_insured_quote6':fields.float('Sum insured', size=64, required=False, readonly=False), 
            'sum_insured_quote7':fields.float('Sum insured', size=64, required=False, readonly=False), 
            'sum_insured_quote8':fields.float('Sum insured', size=64, required=False, readonly=False), 
            'sum_insured_quote9':fields.float('Sum insured', size=64, required=False, readonly=False), 
            'sum_insured_quote10':fields.float('Sum insured', size=64, required=False, readonly=False), 
            'sum_insured_quote11':fields.float('Sum insured', size=64, required=False, readonly=False), 
            'sum_insured_quote12':fields.float('Sum insured', size=64, required=False, readonly=False), 
            'sum_insured_quote13':fields.float('Sum insured', size=64, required=False, readonly=False), 
            'sum_insured_quote14':fields.float('Sum insured', size=64, required=False, readonly=False), 
            'sum_insured_quote15':fields.float('Sum insured', size=64, required=False, readonly=False), 
            'sum_insured_quote16':fields.float('Sum insured', size=64, required=False, readonly=False), 
            'sum_insured_quote17':fields.float('Sum insured', size=64, required=False, readonly=False), 
            'sum_insured_quote18':fields.float('Sum insured', size=64, required=False, readonly=False), 
            'sum_insured_quote19':fields.float('Sum insured', size=64, required=False, readonly=False), 
            'sum_insured_quote20':fields.float('Sum insured', size=64, required=False, readonly=False), 
            'sum_insured_quote21':fields.float('Sum insured', size=64, required=False, readonly=False),
            'sum_insured_quote22':fields.float('Sum insured', size=64, required=False, readonly=False), 
            'sum_insured_quote23':fields.float('Sum insured', size=64, required=False, readonly=False),    
            'period_quote':fields.text('Cancelation Period Conditions',size=64,required=False),
            'period_quote1':fields.text('Cancelation Period Conditions',size=64,required=False),                
            'busines_quote':fields.char('Insured business', size=128, required=False),
            'busines_quote1':fields.char('Insured business', size=128, required=False),
            'person_quote':fields.integer('Insured Persons',size=64,required=False),
            'person_quote1':fields.integer('Insured Persons',size=64,required=False),
            'ocupancy_quote':fields.integer('Occupancy',size=64,required=False),
            'ocupancy_quote1':fields.integer('Occupancy',size=64,required=False),
            'ocupancy_quote2':fields.integer('Occupancy',size=64,required=False),
            'ocupancy_quote3':fields.integer('Occupancy',size=64,required=False),
            'ocupancy_quote4':fields.integer('Occupancy',size=64,required=False),
            'ocupancy_quote5':fields.integer('Occupancy',size=64,required=False),
            'ocupancy_quote6':fields.integer('Occupancy',size=64,required=False),
            'ocupancy_quote7':fields.integer('Occupancy',size=64,required=False),
            'ocupancy_quote8':fields.integer('Occupancy',size=64,required=False),
            'ocupancy_quote9':fields.integer('Occupancy',size=64,required=False),
            'ocupancy_quote10':fields.integer('Occupancy',size=64,required=False),
            'ocupancy_quote11':fields.integer('Occupancy',size=64,required=False),
            'ocupancy_quote12':fields.integer('Occupancy',size=64,required=False),
            'voyage_quote':fields.char('Voyage', size=128, required=False),
            'voyage_quote1':fields.char('Voyage', size=128, required=False),                
            'limit_quote':fields.integer('Limit',size=64,required=False),
            'limit_quote1':fields.integer('Limit',size=64,required=False),
            'limit_quote2':fields.integer('Limit',size=64,required=False),
            'name_quote':fields.char('Cover Name', size=128, required=False),
            'name_quote1':fields.char('Cover Name', size=128, required=False),
            'name_quote2':fields.char('Cover Name', size=128, required=False),     
            'liability_quote':fields.integer('Limit Of Liability',size=64,required=False),
            'liability_quote1':fields.integer('Limit Of Liability',size=64,required=False),
            'xtensions_quote':fields.date('Extensions',required=False,size=32),
            'xtensions_quote1':fields.date('Extensions',required=False,size=32),
            'xtensions_quote2':fields.date('Extensions',required=False,size=32),
            'xtensions_quote3':fields.date('Extensions',required=False,size=32),
            'benefit_quote':fields.char('Benefits covered', size=128, required=False),
            'benefit_quote1':fields.char('Benefits covered', size=128, required=False),
            'benefit_quote2':fields.char('Benefits covered', size=128, required=False),
            'benefit_quote3':fields.char('Benefits covered', size=128, required=False),
            'benefit_quote4':fields.char('Benefits covered', size=128, required=False),
            'benefit_quote5':fields.char('Benefits covered', size=128, required=False),
            'benefit_quote6':fields.char('Benefits covered', size=128, required=False),
            'benefit_quote7':fields.char('Benefits covered', size=128, required=False),
            'benefit_quote8':fields.char('Benefits covered', size=128, required=False),
            'benefit_quote9':fields.char('Benefits covered', size=128, required=False),
            'benefit_quote10':fields.char('Benefits covered', size=128, required=False),
            'benefit_quote11':fields.char('Benefits covered', size=128, required=False),
            'benefit_quote12':fields.char('Benefits covered', size=128, required=False),
            'benefit_quote13':fields.char('Benefits covered', size=128, required=False),
            'benefit_quote14':fields.char('Benefits covered', size=128, required=False),
            'benefit_quote15':fields.char('Benefits covered', size=128, required=False),
            'benefit_quote16':fields.char('Benefits covered', size=128, required=False),
            'benefit_quote17':fields.char('Benefits covered', size=128, required=False),
            'benefit_quote18':fields.char('Benefits covered', size=128, required=False),
            'benefit_quote19':fields.char('Benefits covered', size=128, required=False),
            'benefit_quote20':fields.char('Benefits covered', size=128, required=False),
            'benefit_quote21':fields.char('Benefits covered', size=128, required=False),
            'benefit_quote22':fields.char('Benefits covered', size=128, required=False),
            'rate_quote':fields.float('Rate', size=64, required=False, readonly=False),
            'rate_quote1':fields.float('Rate', size=64, required=False, readonly=False),
            ################################################################################# 
            'tc1':fields.text('Terms and Conditions', size=128, required=False),
            'wording1':fields.text('Wording', size=128, required=False),
            'tc2':fields.text('Terms and Conditions', size=128, required=False),
            'wording2':fields.text('Wording', size=128, required=False),
            'tc3':fields.text('Terms and Conditions', size=128, required=False),
            'wording3':fields.text('Wording', size=128, required=False),
            'tc4':fields.text('Terms and Conditions', size=128, required=False),
            'wording4':fields.text('Wording', size=128, required=False),
            'tc5':fields.text('Terms and Conditions', size=128, required=False),
            'wording5':fields.text('Wording', size=128, required=False),
            'tc6':fields.text('Terms and Conditions', size=128, required=False),
            'wording6':fields.text('Wording', size=128, required=False),
            'tc7':fields.text('Terms and Conditions', size=128, required=False),
            'wording7':fields.text('Wording', size=128, required=False),
            'tc8':fields.text('Terms and Conditions', size=128, required=False),
            'wording8':fields.text('Wording', size=128, required=False),
            'tc9':fields.text('Terms and Conditions', size=128, required=False),
            'wording9':fields.text('Wording', size=128, required=False),
            'tc10':fields.text('Terms and Conditions', size=128, required=False),
            'wording10':fields.text('Wording', size=128, required=False),
            'tc11':fields.text('Terms and Conditions', size=128, required=False),
            'wording11':fields.text('Wording', size=128, required=False),
            'tc12':fields.text('Terms and Conditions', size=128, required=False),
            'wording12':fields.text('Wording', size=128, required=False),
            'tc13':fields.text('Terms and Conditions', size=128, required=False),
            'wording13':fields.text('Wording', size=128, required=False),
            'tc14':fields.text('Terms and Conditions', size=128, required=False),
            'wording14':fields.text('Wording', size=128, required=False),
            'tc15':fields.text('Terms and Conditions', size=128, required=False),
            'wording15':fields.text('Wording', size=128, required=False),
            'tc16':fields.text('Terms and Conditions', size=128, required=False),
            'wording16':fields.text('Wording', size=128, required=False),
            'tc17':fields.text('Terms and Conditions', size=128, required=False),
            'wording17':fields.text('Wording', size=128, required=False),
            'tc18':fields.text('Terms and Conditions', size=128, required=False),
            'wording18':fields.text('Wording', size=128, required=False),
            'tc19':fields.text('Terms and Conditions', size=128, required=False),
            'wording19':fields.text('Wording', size=128, required=False),
            'tc20':fields.text('Terms and Conditions', size=128, required=False),
            'wording20':fields.text('Wording', size=128, required=False),
            'tc21':fields.text('Terms and Conditions', size=128, required=False),
            'wording21':fields.text('Wording', size=128, required=False),
            'tc22':fields.text('Terms and Conditions', size=128, required=False),
            'wording22':fields.text('Wording', size=128, required=False),
            'tc23':fields.text('Terms and Conditions', size=128, required=False),
            'wording23':fields.text('Wording', size=128, required=False),
            'tc24':fields.text('Terms and Conditions', size=128, required=False),
            'wording24':fields.text('Wording', size=128, required=False),
            'tc25':fields.text('Terms and Conditions', size=128, required=False),
            'wording25':fields.text('Wording', size=128, required=False),
        }
sale_order_line()

####################################################################################################################

class product(osv.osv):

    _inherit='product.template'
    
    _product_category_selection = [
        ('erection_all_risks','Erection All Risks'),       
        ('contractor_all_risks','Contractor All Risks'),
        ('third_party_liability','Third Party Liability'),
        ('public_liability_insurance','Public Liability Insurance'),
        ('fire_allied_perils_theft','Fire, Allied Perils & Theft'),
        ('individual_medical_expenses','Individual Medical Expenses'),
        ('plant_all_risk','Plant All Risk'),
        ('money','Money'),
        ('personal_accident','Personal Accident'), 
        ('marine_cargo','Marine Cargo'),
        ('non_binding_indication','Non Binding Indication'), 
        ('property_all_risks','Property All Risks'),  
        ('fidelity','Fidelity'), 
        ('terrorism_liability','Terrorism Liability'), 
        ('sabotage_terrorism','Sabotage & Terrorism'), 
        ('machinery_breakdown','Machinery Breakdown'), 
        ('motor','Motor'),   
        ('property_contents','Property Contents'),
        ('marine_hull','Marine Hull'),
        ('group_life','Group Life'),
        ('travel','Travel'),
        ('professional_indemnity','Professional Indemnity'),
        ('property_fire','Property Fire'),
        ('director_and_officer_liability','Director and Officer Liability'),
        ('miscellaneous','Miscellaneous'),
    ]
    
    _columns = {   
            'product_category_select': fields.selection(_product_category_selection, 'Policy category'),
            'insured_amt_product':fields.float('Insured Amount', size=64, required=False, readonly=False),
            'period_insured_product':fields.date('Period Insured',required=False,size=32),           
            'premium_cost_product':fields.float('Premium',size=64, required=False, readonly=False),
            'deductable_product':fields.float('Deductable',size=64, required=False, readonly=False),
            'com_product':fields.float('Commission', size=64, required=False, readonly=False),
            'agent_product':fields.float('Agent Commission', size=64, required=False, readonly=False),              
            'policy_ref_product':fields.char('Policy Reference', size=64, required=False, readonly=False),           
            'wording_product':fields.text('Wording', size=128, required=False,readonly=False),
             #
            'Vehicle_quote_product':fields.char('Insured Vehicle', size=128, required=False), 
            'situation_quote_product':fields.text('Situation',size=64,required=False),
            'limit_los_quote_product':fields.integer('Loss limit',size=64,required=False),
            'car_quote_product':fields.char('Cargo', size=128, required=False),
            'des_quote_product':fields.char('Destination', size=128, required=False),
            'plan_quote_product':fields.char('Name Of Plan', size=128, required=False),
            'xcess_quote_product':fields.integer('Excess',size=64,required=False),
            'work_quote_product':fields.text('Scope Of Work', size=128, required=False),
            'bov_quote_product':fields.integer('B.O.V',size=64,required=False),
            # Additional Datas
            'sum_insured_quote_product':fields.float('Sum insured', size=64, required=False, readonly=False),
            'sum_insured_quote_product1':fields.float('Sum insured', size=64, required=False, readonly=False), 
            'sum_insured_quote_product2':fields.float('Sum insured', size=64, required=False, readonly=False), 
            'sum_insured_quote_product3':fields.float('Sum insured', size=64, required=False, readonly=False), 
            'sum_insured_quote_product4':fields.float('Sum insured', size=64, required=False, readonly=False), 
            'sum_insured_quote_product5':fields.float('Sum insured', size=64, required=False, readonly=False), 
            'sum_insured_quote_product6':fields.float('Sum insured', size=64, required=False, readonly=False), 
            'sum_insured_quote_product7':fields.float('Sum insured', size=64, required=False, readonly=False), 
            'sum_insured_quote_product8':fields.float('Sum insured', size=64, required=False, readonly=False), 
            'sum_insured_quote_product9':fields.float('Sum insured', size=64, required=False, readonly=False), 
            'sum_insured_quote_product10':fields.float('Sum insured', size=64, required=False, readonly=False), 
            'sum_insured_quote_product11':fields.float('Sum insured', size=64, required=False, readonly=False), 
            'sum_insured_quote_product12':fields.float('Sum insured', size=64, required=False, readonly=False), 
            'sum_insured_quote_product13':fields.float('Sum insured', size=64, required=False, readonly=False), 
            'sum_insured_quote_product14':fields.float('Sum insured', size=64, required=False, readonly=False), 
            'sum_insured_quote_product15':fields.float('Sum insured', size=64, required=False, readonly=False), 
            'sum_insured_quote_product16':fields.float('Sum insured', size=64, required=False, readonly=False), 
            'sum_insured_quote_product17':fields.float('Sum insured', size=64, required=False, readonly=False), 
            'sum_insured_quote_product18':fields.float('Sum insured', size=64, required=False, readonly=False), 
            'sum_insured_quote_product19':fields.float('Sum insured', size=64, required=False, readonly=False), 
            'sum_insured_quote_product20':fields.float('Sum insured', size=64, required=False, readonly=False), 
            'sum_insured_quote_product21':fields.float('Sum insured', size=64, required=False, readonly=False),
            'sum_insured_quote_product22':fields.float('Sum insured', size=64, required=False, readonly=False), 
            'sum_insured_quote_product23':fields.float('Sum insured', size=64, required=False, readonly=False),    
            'period_quote_product':fields.text('Cancelation Period Conditions',size=64,required=False),
            'period_quote_product1':fields.text('Cancelation Period Conditions',size=64,required=False),                
            'busines_quote_product':fields.char('Insured business', size=128, required=False),
            'busines_quote_product1':fields.char('Insured business', size=128, required=False),
            'person_quote_product':fields.integer('Insured Persons',size=64,required=False),
            'person_quote_product1':fields.integer('Insured Persons',size=64,required=False),
            'ocupancy_quote_product':fields.integer('Occupancy',size=64,required=False),
            'ocupancy_quote_product1':fields.integer('Occupancy',size=64,required=False),
            'ocupancy_quote_product2':fields.integer('Occupancy',size=64,required=False),
            'ocupancy_quote_product3':fields.integer('Occupancy',size=64,required=False),
            'ocupancy_quote_product4':fields.integer('Occupancy',size=64,required=False),
            'ocupancy_quote_product5':fields.integer('Occupancy',size=64,required=False),
            'ocupancy_quote_product6':fields.integer('Occupancy',size=64,required=False),
            'ocupancy_quote_product7':fields.integer('Occupancy',size=64,required=False),
            'ocupancy_quote_product8':fields.integer('Occupancy',size=64,required=False),
            'ocupancy_quote_product9':fields.integer('Occupancy',size=64,required=False),
            'ocupancy_quote_product10':fields.integer('Occupancy',size=64,required=False),
            'ocupancy_quote_product11':fields.integer('Occupancy',size=64,required=False),
            'ocupancy_quote_product12':fields.integer('Occupancy',size=64,required=False),
            'voyage_quote_product':fields.char('Voyage', size=128, required=False),
            'voyage_quote_product1':fields.char('Voyage', size=128, required=False),                
            'limit_quote_product':fields.integer('Limit',size=64,required=False),
            'limit_quote_product1':fields.integer('Limit',size=64,required=False),
            'limit_quote_product2':fields.integer('Limit',size=64,required=False),
            'name_quote_product':fields.char('Cover Name', size=128, required=False),
            'name_quote_product1':fields.char('Cover Name', size=128, required=False),
            'name_quote_product2':fields.char('Cover Name', size=128, required=False),     
            'liability_quote_product':fields.integer('Limit Of Liability',size=64,required=False),
            'liability_quote_product1':fields.integer('Limit Of Liability',size=64,required=False),
            'xtensions_quote_product':fields.date('Extensions',required=False,size=32),
            'xtensions_quote_product1':fields.date('Extensions',required=False,size=32),
            'xtensions_quote_product2':fields.date('Extensions',required=False,size=32),
            'xtensions_quote_product3':fields.date('Extensions',required=False,size=32),
            'benefit_quote_product':fields.char('Benefits covered', size=128, required=False),
            'benefit_quote_product1':fields.char('Benefits covered', size=128, required=False),
            'benefit_quote_product2':fields.char('Benefits covered', size=128, required=False),
            'benefit_quote_product3':fields.char('Benefits covered', size=128, required=False),
            'benefit_quote_product4':fields.char('Benefits covered', size=128, required=False),
            'benefit_quote_product5':fields.char('Benefits covered', size=128, required=False),
            'benefit_quote_product6':fields.char('Benefits covered', size=128, required=False),
            'benefit_quote_product7':fields.char('Benefits covered', size=128, required=False),
            'benefit_quote_product8':fields.char('Benefits covered', size=128, required=False),
            'benefit_quote_product9':fields.char('Benefits covered', size=128, required=False),
            'benefit_quote_product10':fields.char('Benefits covered', size=128, required=False),
            'benefit_quote_product11':fields.char('Benefits covered', size=128, required=False),
            'benefit_quote_product12':fields.char('Benefits covered', size=128, required=False),
            'benefit_quote_product13':fields.char('Benefits covered', size=128, required=False),
            'benefit_quote_product14':fields.char('Benefits covered', size=128, required=False),
            'benefit_quote_product15':fields.char('Benefits covered', size=128, required=False),
            'benefit_quote_product16':fields.char('Benefits covered', size=128, required=False),
            'benefit_quote_product17':fields.char('Benefits covered', size=128, required=False),
            'benefit_quote_product18':fields.char('Benefits covered', size=128, required=False),
            'benefit_quote_product19':fields.char('Benefits covered', size=128, required=False),
            'benefit_quote_product20':fields.char('Benefits covered', size=128, required=False),
            'benefit_quote_product21':fields.char('Benefits covered', size=128, required=False),
            'benefit_quote_product22':fields.char('Benefits covered', size=128, required=False),
            'rate_quote_product':fields.float('Rate', size=64, required=False, readonly=False),
            'rate_quote_product1':fields.float('Rate', size=64, required=False, readonly=False),  
            }
    #_defaults = {
        #'wording_product': 'Every Client is assigned a personal Account Handler who deals with all needs and requirements on a '
                #'daily basis, and focuses on keeping the client informed through the entire process.',
       # }
product()

class crm_lead(osv.osv):
    
    _inherit='crm.lead'
    
    _product_selection = [
        ('erection_all_risks','Erection All Risks'),       
        ('contractor_all_risks','Contractor All Risks'),
        ('third_party_liability','Third Party Liability'),
        ('public_liability_insurance','Public Liability Insurance'),
        ('fire_allied_perils_theft','Fire, Allied Perils & Theft'),
        ('individual_medical_expenses','Individual Medical Expenses'),
        ('plant_all_risk','Plant All Risk'),
        ('money','Money'),
        ('personal_accident','Personal Accident'), 
        ('marine_cargo','Marine Cargo'),
        ('non_binding_indication','Non Binding Indication'), 
        ('property_all_risks','Property All Risks'),  
        ('fidelity','Fidelity'), 
        ('terrorism_liability','Terrorism Liability'), 
        ('sabotage_terrorism','Sabotage & Terrorism'), 
        ('machinery_breakdown','Machinery Breakdown'), 
        ('motor','Motor'),   
        ('property_contents','Property Contents'),
        ('marine_hull','Marine Hull'),
        ('group_life','Group Life'),
        ('travel','Travel'),
        ('professional_indemnity','Professional Indemnity'),
        ('property_fire','Property Fire'),
        ('director_and_officer_liability','Director and Officer Liability'),
        ('miscellaneous','Miscellaneous'),
    ]
    
    _columns = {
            #Datas in Lead
            'product_select': fields.selection(_product_selection, 'Policy type'),
            #'product':fields.many2one('product.product','Product',size=32,required=False),
            #'insured_amt_crm_lead':fields.float('Insured', size=64, required=False, readonly=False),
            'period_insured_crm_lead':fields.date('Period Insured',required=False,size=32),
            'premium_cost_crm_lead':fields.float('Premium',size=64, required=False, readonly=False), 
            'deductable_crm_lead':fields.float('Deductable',size=64, required=False, readonly=False),
            'wording_crm_lead':fields.text('Wording', size=128, required=False,readonly=False),
            #
            'territorial_area_crm_lead':fields.many2one('res.country','Territorial Area',size=32,required=False),
            'loss_limit_crm_lead':fields.float('Loss limits',size=64,required=False),
            'Cargo_crm_lead':fields.char('Cargo', size=128, required=False),
            'bov_crm_lead':fields.integer('B.O.V',size=64,required=False),
            'vehicle_type_crm_lead':fields.char('Vehicle type', size=64, required=False, readonly=False),
            'vehicle_reg_no_crm_lead':fields.char('Vehicle Registration no.', size=64, required=False, readonly=False),
            'cover_name_crm_lead':fields.char('Cover Name', size=128, required=False),
            'driving_exp_crm_lead':fields.integer('Driving experience',size=64,required=False), 
            'special': fields.text('Special Remarks',size=64, required=False, readonly=False),
            # Additional Datas in Lead
            'sum_insured_crm_lead':fields.float('Sum insured', size=64, required=False, readonly=False), 
            'sum_insured_crm_lead1':fields.float('Sum insured', size=64, required=False, readonly=False),
            'sum_insured_crm_lead2':fields.float('Sum insured', size=64, required=False, readonly=False),
            'sum_insured_crm_lead3':fields.float('Sum insured', size=64, required=False, readonly=False),
            'sum_insured_crm_lead4':fields.float('Sum insured', size=64, required=False, readonly=False),
            'sum_insured_crm_lead5':fields.float('Sum insured', size=64, required=False, readonly=False),
            'sum_insured_crm_lead6':fields.float('Sum insured', size=64, required=False, readonly=False),
            'sum_insured_crm_lead7':fields.float('Sum insured', size=64, required=False, readonly=False),
            'sum_insured_crm_lead8':fields.float('Sum insured', size=64, required=False, readonly=False),
            'sum_insured_crm_lead9':fields.float('Sum insured', size=64, required=False, readonly=False),
            'sum_insured_crm_lead10':fields.float('Sum insured', size=64, required=False, readonly=False),
            'sum_insured_crm_lead11':fields.float('Sum insured', size=64, required=False, readonly=False),
            'sum_insured_crm_lead12':fields.float('Sum insured', size=64, required=False, readonly=False),
            'sum_insured_crm_lead13':fields.float('Sum insured', size=64, required=False, readonly=False),
            'sum_insured_crm_lead14':fields.float('Sum insured', size=64, required=False, readonly=False),
            'sum_insured_crm_lead15':fields.float('Sum insured', size=64, required=False, readonly=False),
            'sum_insured_crm_lead16':fields.float('Sum insured', size=64, required=False, readonly=False),
            'sum_insured_crm_lead17':fields.float('Sum insured', size=64, required=False, readonly=False),                    
            'scope_ofwork_crm_lead':fields.text('Scope Of Work', size=128, required=False),
            'scope_ofwork_crm_lead1':fields.text('Scope Of Work', size=128, required=False),
            'territorial_limit_crm_lead':fields.char('Territorial limits', size=64, required=False, readonly=False),
            'territorial_limit_crm_lead1':fields.char('Territorial limits', size=64, required=False, readonly=False),
            'territorial_limit_crm_lead2':fields.char('Territorial limits', size=64, required=False, readonly=False),
            'territorial_limit_crm_lead3':fields.char('Territorial limits', size=64, required=False, readonly=False),
            'territorial_limit_crm_lead4':fields.char('Territorial limits', size=64, required=False, readonly=False),                
            'liability_crm_lead':fields.integer('Limits Of Liability',size=64,required=False),
            'liability_crm_lead1':fields.integer('Limits Of Liability',size=64,required=False),
            'maximum_limit_crm_lead':fields.integer('Maximum Limit',size=64,required=False),
            'maximum_limit_crm_lead1':fields.integer('Maximum Limit',size=64,required=False),
            'benefit_crm_lead':fields.char('Benefits covered', size=128, required=False),
            'benefit_crm_lead1':fields.char('Benefits covered', size=128, required=False),
            'benefit_crm_lead2':fields.char('Benefits covered', size=128, required=False),
            'benefit_crm_lead3':fields.char('Benefits covered', size=128, required=False),
            'benefit_crm_lead4':fields.char('Benefits covered', size=128, required=False),
            'benefit_crm_lead5':fields.char('Benefits covered', size=128, required=False),
            'benefit_crm_lead6':fields.char('Benefits covered', size=128, required=False),
            'benefit_crm_lead7':fields.char('Benefits covered', size=128, required=False),
            'benefit_crm_lead8':fields.char('Benefits covered', size=128, required=False),
            'benefit_crm_lead9':fields.char('Benefits covered', size=128, required=False),
            'benefit_crm_lead10':fields.char('Benefits covered', size=128, required=False),
            'benefit_crm_lead11':fields.char('Benefits covered', size=128, required=False),
            'benefit_crm_lead12':fields.char('Benefits covered', size=128, required=False),
            'benefit_crm_lead13':fields.char('Benefits covered', size=128, required=False),
            'benefit_crm_lead14':fields.char('Benefits covered', size=128, required=False),
            'benefit_crm_lead15':fields.char('Benefits covered', size=128, required=False),
            'benefit_crm_lead16':fields.char('Benefits covered', size=128, required=False),
            'benefit_crm_lead17':fields.char('Benefits covered', size=128, required=False),
            'benefit_crm_lead18':fields.char('Benefits covered', size=128, required=False),
            'benefit_crm_lead19':fields.char('Benefits covered', size=128, required=False),
            'limit_crm_lead':fields.float('Limits',size=64,required=False),
            'limit_crm_lead1':fields.float('Limits',size=64,required=False),
            'limit_crm_lead2':fields.float('Limits',size=64,required=False),
            'limit_crm_lead3':fields.float('Limits',size=64,required=False),                
            'cancel_period_crm_lead':fields.text('Cancelation Period Conditions',size=64,required=False),
            'cancel_period_crm_lead1':fields.text('Cancelation Period Conditions',size=64,required=False),
            'interest_crm_lead':fields.float('Interest',size=64,required=False),
            'interest_crm_lead1':fields.float('Interest',size=64,required=False),
            'interest_crm_lead2':fields.float('Interest',size=64,required=False),
            'voyage_crm_lead':fields.char('Voyage', size=128, required=False),
            'voyage_crm_lead1':fields.char('Voyage', size=128, required=False),                
            'rate_crm_lead':fields.float('Rate', size=64, required=False, readonly=False),
            'rate_crm_lead1':fields.float('Rate', size=64, required=False, readonly=False),
            'xcess_crm_lead':fields.integer('Excess',size=64,required=False),
            'xcess_crm_lead1':fields.integer('Excess',size=64,required=False),
            'xtensions_crm_lead':fields.date('Extensions',required=False,size=32),
            'xtensions_crm_lead1':fields.date('Extensions',required=False,size=32),
            'xtensions_crm_lead2':fields.date('Extensions',required=False,size=32),
            'xtensions_crm_lead3':fields.date('Extensions',required=False,size=32),
            'xtensions_crm_lead4':fields.date('Extensions',required=False,size=32), 
            ########################################################################
            'Policy':fields.integer('Policy No:', size=64, required=False, readonly=False),
            'type':fields.char('Type', size=64, required=False, readonly=False),
            'summary':fields.text('Summary',size=64,required=False),
            #############################################################################
            'tc_crm_lead1':fields.text('Terms and Conditions', size=128, required=False),
            'wording_crm_lead1':fields.text('Wording', size=128, required=False),
            'tc_crm_lead2':fields.text('Terms and Conditions', size=128, required=False),
            'wording_crm_lead2':fields.text('Wording', size=128, required=False),
            'tc_crm_lead3':fields.text('Terms and Conditions', size=128, required=False),
            'wording_crm_lead3':fields.text('Wording', size=128, required=False),
            'tc_crm_lead4':fields.text('Terms and Conditions', size=128, required=False),
            'wording_crm_lead4':fields.text('Wording', size=128, required=False),
            'tc_crm_lead5':fields.text('Terms and Conditions', size=128, required=False),
            'wording_crm_lead5':fields.text('Wording', size=128, required=False),
            'tc_crm_lead6':fields.text('Terms and Conditions', size=128, required=False),
            'wording_crm_lead6':fields.text('Wording', size=128, required=False),
            'tc_crm_lead7':fields.text('Terms and Conditions', size=128, required=False),
            'wording_crm_lead7':fields.text('Wording', size=128, required=False),
            'tc_crm_lead8':fields.text('Terms and Conditions', size=128, required=False),
            'wording_crm_lead8':fields.text('Wording', size=128, required=False),
            'tc_crm_lead9':fields.text('Terms and Conditions', size=128, required=False),
            'wording_crm_lead9':fields.text('Wording', size=128, required=False),
            'tc_crm_lead10':fields.text('Terms and Conditions', size=128, required=False),
            'wording_crm_lead10':fields.text('Wording', size=128, required=False),
            'tc_crm_lead11':fields.text('Terms and Conditions', size=128, required=False),
            'wording_crm_lead11':fields.text('Wording', size=128, required=False),
            'tc_crm_lead12':fields.text('Terms and Conditions', size=128, required=False),
            'wording_crm_lead12':fields.text('Wording', size=128, required=False),
            'tc_crm_lead13':fields.text('Terms and Conditions', size=128, required=False),
            'wording_crm_lead13':fields.text('Wording', size=128, required=False),
            'tc_crm_lead14':fields.text('Terms and Conditions', size=128, required=False),
            'wording_crm_lead14':fields.text('Wording', size=128, required=False),
            'tc_crm_lead15':fields.text('Terms and Conditions', size=128, required=False),
            'wording_crm_lead15':fields.text('Wording', size=128, required=False),
            'tc_crm_lead16':fields.text('Terms and Conditions', size=128, required=False),
            'wording_crm_lead16':fields.text('Wording', size=128, required=False),
            'tc_crm_lead17':fields.text('Terms and Conditions', size=128, required=False),
            'wording_crm_lead17':fields.text('Wording', size=128, required=False),
            'tc_crm_lead18':fields.text('Terms and Conditions', size=128, required=False),
            'wording_crm_lead18':fields.text('Wording', size=128, required=False),
            'tc_crm_lead19':fields.text('Terms and Conditions', size=128, required=False),
            'wording_crm_lead19':fields.text('Wording', size=128, required=False),
            'tc_crm_lead20':fields.text('Terms and Conditions', size=128, required=False),
            'wording_crm_lead20':fields.text('Wording', size=128, required=False),
            'tc_crm_lead21':fields.text('Terms and Conditions', size=128, required=False),
            'wording_crm_lead21':fields.text('Wording', size=128, required=False),
            'tc_crm_lead22':fields.text('Terms and Conditions', size=128, required=False),
            'wording_crm_lead22':fields.text('Wording', size=128, required=False),        
            'tc_crm_lead23':fields.text('Terms and Conditions', size=128, required=False),
            'wording_crm_lead23':fields.text('Wording', size=128, required=False),
            'tc_crm_lead24':fields.text('Terms and Conditions', size=128, required=False),
            'wording_crm_lead24':fields.text('Wording', size=128, required=False),
            'tc_crm_lead25':fields.text('Terms and Conditions', size=128, required=False),
            'wording_crm_lead25':fields.text('Wording', size=128, required=False),
                           
        }
    
    #_defaults = {
       # 'wording_crm_lead': 'Every Client is assigned a personal Account Handler who deals with all needs and requirements on a daily basis, and focuses on keeping the client informed through the entire process.',
       # }         
crm_lead()

class sale_customer(osv.osv):

    _inherit='res.partner'
 
    _columns = {
            'customer_correspondence': fields.one2many('crm.lead', 'partner_id', 'Correspondence'),
            'customer_current_deal': fields.one2many('account.invoice', 'partner_id', 'Current Dealings'),
            'customer_uncomple_deal': fields.one2many('sale.order', 'partner_id', 'Incomplete Dealings'),
            'customer_claim_history': fields.one2many('crm.claim', 'partner_id', 'Claim History'),
            'customer_dob': fields.date('D.O.B'),
            'insurence_agent':fields.char('Agent', size=64, required=False, readonly=False), 
        }
sale_customer()

class crm_claim(osv.osv):
     
    _inherit = 'crm.claim'
     
    def create(self, cr, uid, vals, context=None):        
        vals['sequence'] = self.pool.get('ir.sequence').get(cr,uid,'QWE')
        return super(crm_claim, self).create(cr, uid, vals, context)
    
    _product_selection = [
        ('erection_all_risks','Erection All Risks'),       
        ('contractor_all_risks','Contractor All Risks'),
        ('third_party_liability','Third Party Liability'),
        ('public_liability_insurance','Public Liability Insurance'),
        ('fire_allied_perils_theft','Fire, Allied Perils & Theft'),
        ('individual_medical_expenses','Individual Medical Expenses'),
        ('plant_all_risk','Plant All Risk'),
        ('money','Money'),
        ('personal_accident','Personal Accident'), 
        ('marine_cargo','Marine Cargo'),
        ('non_binding_indication','Non Binding Indication'), 
        ('property_all_risks','Property All Risks'),  
        ('fidelity','Fidelity'), 
        ('terrorism_liability','Terrorism Liability'), 
        ('sabotage_terrorism','Sabotage & Terrorism'), 
        ('machinery_breakdown','Machinery Breakdown'), 
        ('motor','Motor'),   
        ('property_contents','Property Contents'),
        ('marine_hull','Marine Hull'),
        ('group_life','Group Life'),
        ('travel','Travel'),
        ('professional_indemnity','Professional Indemnity'),
        ('property_fire','Property Fire'),
        ('director_and_officer_liability','Director and Officer Liability'),
        ('miscellaneous','Miscellaneous'),
    ]
       
    _columns = {
            'Partner':fields.char('Partner No:', size=64, required=False, readonly=False),
            'Policy':fields.integer('Policy No:', size=64, required=False, readonly=False),            
            'sequence':fields.char('Claim No:', size=64, required=False, readonly=False),
            'crm_claim_product':fields.selection(_product_selection,'Policy type', size=64, required=False, readonly=False),
            'claim_amount':fields.float('Claim Amount',required=True),
            'loss':fields.char('Loss Adjuster', size=64, required=False, readonly=False),
            'insured':fields.float('Insured With',required=True)
            }
crm_claim()