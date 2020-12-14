# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare


class ProductExpense(models.Model):
    _name = 'product.expense'
    _description = 'Product Expense'
    _rec_name = 'name'
    _order = 'name DESC'

    name = fields.Char(string="Name", required=True, copy=False)
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
    quantity = fields.Float(string="Quantity", compute='compute_quantity')
    unit_price = fields.Float(string="Unit Price")

    cost_price = fields.Float(string="Cost Price", compute='compute_cost_price')

    @api.depends('product_id', 'conversion_id',
                 'conversion_id.product_to_remove_ids', 'conversion_id.product_to_remove_ids.quantity')
    def compute_quantity(self):
        for product in self:
            total_quantity = 0.0
            for remove in product.conversion_id.product_to_remove_ids:
                total_quantity += remove.quantity
            if total_quantity:
                product.quantity = total_quantity
            else:
                product.quantity = 0.0

    @api.depends('product_id', 'unit_price', 'quantity')
    def compute_cost_price(self):
        for product in self:
            if product.quantity:
                product.cost_price = product.unit_price * product.quantity
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

                        # def _get_procurement_group(self):
    #     return self.conversion_id.procurement_group_id
    #
    # def _prepare_procurement_group_vals(self):
    #     return {
    #         'name': self.conversion_id.name,
    #         'move_type': 'direct',
    #         'conversion_id': self.conversion_id.id,
    #         'partner_id': self.conversion_id.partner_shipping_id.id,
    #     }
    #
    # def _get_qty_procurement(self, previous_product_uom_qty=False):
    #     self.ensure_one()
    #     qty = 0.0
    #     outgoing_moves, incoming_moves = self._get_outgoing_incoming_moves()
    #     for move in outgoing_moves:
    #         qty += move.product_uom._compute_quantity(move.product_uom_qty, self.product_uom, rounding_method='HALF-UP')
    #     for move in incoming_moves:
    #         qty -= move.product_uom._compute_quantity(move.product_uom_qty, self.product_uom, rounding_method='HALF-UP')
    #     return qty
    #
    # def _get_outgoing_incoming_moves(self):
    #     outgoing_moves = self.env['stock.move']
    #     incoming_moves = self.env['stock.move']
    #
    #     for move in self.move_ids.filtered(
    #             lambda r: r.state != 'cancel' and not r.scrapped and self.product_id == r.product_id):
    #         if move.location_dest_id.usage == "customer":
    #             if not move.origin_returned_move_id or (move.origin_returned_move_id and move.to_refund):
    #                 outgoing_moves |= move
    #         elif move.location_dest_id.usage != "customer" and move.to_refund:
    #             incoming_moves |= move
    #
    #     return outgoing_moves, incoming_moves
    #
    # def _prepare_procurement_values(self, group_id=False):
    #     """ Prepare specific key for moves or other components that will be created from a stock rule
    #     comming from a sale order line. This method could be override in order to add other custom key that could
    #     be used in move/po creation.
    #     """
    #     # values = super(ProductRemove, self)._prepare_procurement_values(group_id)
    #
    #     values = {}
    #
    #     self.ensure_one()
    #     date_planned = self.conversion_id.conversion_date
    #     values.update({
    #         'group_id': group_id,
    #         'product_remove_id': self.id,
    #         'conversion_id': self.conversion_id.id,
    #         'date_planned': date_planned,
    #         'route_ids': self.product_id.route_ids,
    #         'warehouse_id': self.conversion_id.warehouse_id or False,
    #         'partner_id': self.conversion_id.partner_shipping_id.id,
    #         'company_id': self.conversion_id.company_id,
    #     })
    #     return values
