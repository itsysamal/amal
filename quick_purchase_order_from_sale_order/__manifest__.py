# -*- coding: utf-8 -*-
{
    'name': 'Quick Purchase Order From Sales Order',
    'summary': "Quick Create/View Purchase Order From Sales Order",
    'description': "Quick Create/View Purchase Order From Sales Order",

    'author': 'iPredict IT Solutions Pvt. Ltd.',
    'website': 'http://ipredictitsolutions.com',
    'support': 'ipredictitsolutions@gmail.com',

    'category': 'Sales',
    'version': '13.0.0.1.0',
    'depends': ['sale_management', 'purchase','sale_contract_management'],

    'data': [
        'security/quick_purchase_from_sale_security.xml',
        'views/purchase_order_view.xml',
        'views/sale_order_view.xml',
    ],

    'license': "OPL-1",
    'price': 10,
    'currency': "EUR",

    'auto_install': False,
    'installable': True,

    'images': ['static/description/banner.png'],
}
