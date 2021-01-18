# -*- encoding: utf-8 -*-
{
    'name': 'Sale Contract Management',
    'version': '1.0',
    'category': 'Sale',
    'description': """
     Sale Contract Management
    """,
    'summary': 'Sale Contract Management',
    'author': "Doaa Khaled",
    'E-mail': "doaakhaled6969@gmail.com",
    'images': ['static/description/icon.png'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/sequence.xml',
        'views/sale_contract_view.xml',
        'views/sale_contract_line_view.xml',
        'views/sale_contract_operation_lines_view.xml',
        'views/sale_ship_cost_line_view.xml',
        'views/sale_order_view.xml',
        'views/account_payment_view.xml',
        'views/account_move_view.xml',
    ],
    'depends': ['base', 'sale', 'product', 'account', 'branch', 'product_brand_inventory',
                'eq_sale_advance_payment', 'gio_product_analytic','sales_team'],
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 106,
    'WBS': 'AML-36',
}
