# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare


class ProductExpense(models.Model):
    _name = 'product.expense'
    _description = 'Product Expense'
    _rec_name = 'name'
    _order = 'name DESC'

    name = fields.Char(string="Name", required=True, default="Product Conversion")
    conversion_id = fields.Many2one('product.conversion', string="Product Conversion")
    product_id = fields.Many2one('product.product', string="Product", required=True,
                                 domain=[('type', 'in', ('consu', 'service'))])
    product_tmp_id = fields.Many2one('product.template', related='product_id.product_tmpl_id',
                                     string="Product Template", store=True)
    analytic_account_id = fields.Many2one("account.analytic.account", related='product_id.gio_analytic_account',
                                          store=True, string='Analytic Account')
    analytic_tag_ids = fields.Many2one("account.analytic.tag", string='Analytic Tags', store=True,
                                       related='product_id.gio_analytic_tag')
    product_uom = fields.Many2one('uom.uom', string='UOM',
                                  domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=True)
    branch_id = fields.Many2one('res.branch', string='Branch')
    quantity = fields.Float(string="Quantity", compute='compute_quantity', digits=(12, 3))
    quantity_type = fields.Selection([('fixed', 'Fixed'),
                                      ('compute', 'Computed')],
                                     'Quantity Type', required=True,
                                     copy=False, tracking=True)
    change_quantity = fields.Float(string="Fixed Quantity")
    unit_price = fields.Float(string="Unit Price", digits=(12, 3))

    cost_price = fields.Float(string="Cost Price", compute='compute_cost_price', digits=(12, 3))

    @api.depends('product_id', 'conversion_id', 'quantity_type',
                 'conversion_id.product_to_remove_ids', 'conversion_id.product_to_remove_ids.quantity')
    def compute_quantity(self):
        for product in self:
            total_quantity = 0.0
            for remove in product.conversion_id.product_to_remove_ids:
                total_quantity += remove.quantity
            if total_quantity and product.quantity_type == 'compute':
                product.quantity = total_quantity
            else:
                product.quantity = 0.0

    @api.depends('product_id', 'unit_price', 'quantity', 'change_quantity', 'quantity_type')
    def compute_cost_price(self):
        for product in self:
            if product.quantity and product.quantity_type == 'compute':
                product.cost_price = product.unit_price * product.quantity
            elif product.change_quantity and product.quantity_type == 'fixed':
                product.cost_price = product.unit_price * product.change_quantity
            else:
                product.cost_price = 0.0

    @api.constrains('quantity')
    def quantity_percentage_not_minus(self):
        for product in self:
            if product.quantity < 0:
                raise ValidationError('Please enter a positive number in Quantity')

    @api.onchange('product_id', 'quantity')
    def onchange_product_id(self):
        if self.product_id:
            self.product_uom = self.product_id.uom_id
            self.analytic_account_id = self.product_id.gio_analytic_account
            self.analytic_tag_ids = self.product_id.gio_analytic_tag
