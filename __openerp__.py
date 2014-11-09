{
    "name" : "INSURANCE",
    "version" : "1.0",
    "depends" : ['sale','account'],
    "author" : "Novasoft Consultancy Services Pvt. Ltd.",
    'category' : 'Insurance',
    "description": """ Patrick York Insurance - Management Module
    
    """,
    'website': 'http://www.novasoftindia.com',
    'data': [
             'sale_inherit_view.xml' ,
             'insurance_menu_view.xml',
             'sequence_view.xml',
             'helpdesk_view.xml',
             'account_invoice_inherit_view.xml',
             'rename_opportunity2_slip_view.xml',
             'account_analytic_account_inherit_view.xml'
             ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,

}