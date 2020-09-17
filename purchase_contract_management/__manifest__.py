# -*- encoding: utf-8 -*-
{
    'name': 'Purchase Contract Management',
    'version': '1.0',
    'category': 'Purchase',
    'description': """
     Purchase Contract Management
    """,
    'summary': 'Purchase Contract Management',
    'author': "Doaa Khaled",
    'E-mail': "doaakhaled6969@gmail.com",
    'images': ['static/description/icon.png'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/sequence.xml',
        'views/product_template_view.xml',
        'views/purchase_contract_view.xml',
        'views/purchase_contract_line_view.xml',
        'views/contract_operation_lines_view.xml',
        'views/ship_cost_line_view.xml',
        'views/purchase_order_view.xml',
        'views/account_payment_view.xml',
        'views/account_move_view.xml',
    ],
    'depends': ['base', 'purchase','product','account','branch'],
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 106,
    'WBS': 'AML-27',
}
