# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# Add company_id to Account Checks related to task RWD-19
{
    'name': 'Account Checks',
    'version': '1.0',
    'category': 'Accounting',
    'sequence': 10,
    'author': 'ITSYS CORPORATION',
    'summary': '',
    'description': "Payment through checks",
    'website': 'https://www.it-syscorp.com',
    'depends': ['account_accountant','account'],
    'data': [
        'security/account_check_security.xml',
        'security/ir.model.access.csv',
        'account_check_data.xml',
        'account_check_view.xml',
        'wizard/hash_to_supplier_view.xml',
        'chemical_bank.xml',

    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
