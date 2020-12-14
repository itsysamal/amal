# -*- encoding: utf-8 -*-
{
    'name': 'Product Conversion Management',
    'version': '1.0',
    'category': 'Product',
    'description': """
     Product Conversion Management
    """,
    'summary': 'Product Conversion Management',
    'author': "Doaa Khaled",
    'E-mail': "doaakhaled6969@gmail.com",
    'images': ['static/description/icon.jpg'],
    'data': [
        'security/ir.model.access.csv',
        'views/sequence.xml',
        'views/product_conversion_view.xml',
        'views/product_to_remove_view.xml',
        'views/product_to_add_view.xml',
        'views/stock_picking_view.xml',
    ],
    'depends': ['base','stock','product','account','branch','stock_analytic','stock_analytic_tag'],
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 106,
    'WBS': 'AML-34',
}
