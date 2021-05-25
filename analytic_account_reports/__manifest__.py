# -*- coding: utf-8 -*-
{
    'name': "Analytic Account Reports",
    'summary': """
       Analytic Account Reports    """,
    'author': "doaa",
    'category': 'Accounts',
    'version': '13',
    'depends': ['base',
                'analytic',
                'sale',
                'product',
                'stock',
                'sale_stock',
                'purchase',
                'account',
                'gio_product_analytic',
                'account_budget',
                'account_analytic_parent',
                'report_xlsx',
                ],
    'data': [
        'security/ir.model.access.csv',
        'views/analytic_account_view.xml',
        'report/report.xml',
    ],
}