# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare


class ProductRemove(models.Model):
    _name = 'product.remove'
    _description = 'Product To Remove'
    _rec_name = 'name'
    _order = 'name DESC'

    name = fields.Char(string="Name", required=True,default="Product Conversion")
    conversion_id = fields.Many2one('product.conversion', string="Product Conversion")
    product_id = fields.Many2one('product.product', string="Product", required=True)
    product_tmp_id = fields.Many2one('product.template', related='product_id.product_tmpl_id',
                                     string="Product Template", store=True)
    location_id = fields.Many2one('stock.location', string="Inventory Locations", required=True)
    lot_id = fields.Many2one('stock.production.lot', string="Lot /Serial")
    analytic_account_id = fields.Many2one("account.analytic.account", related='product_id.gio_analytic_account',
                                          store=True, string='Analytic Account')
    analytic_tag_ids = fields.Many2one("account.analytic.tag", string='Analytic Tags', store=True,
                                       related='product_id.gio_analytic_tag')
    product_uom = fields.Many2one('uom.uom', string='UOM',
                                  domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=True)
    branch_id = fields.Many2one('res.branch', string='Branch')
    quantity = fields.Float(string="Quantity", default=1.0)
    remaining_qty = fields.Float(string="Remaining quantity")
    availability = fields.Float(string="Available", store=True)
    fixed_percentage = fields.Selection([('fixed', 'Fixed'),
                                         ('percentage', 'Percentage')],
                                        'Cost Type',
                                        copy=False, tracking=True)
    unit_price = fields.Float(string="Unit Price", compute='compute_unit_price')

    cost_price = fields.Float(string="Cost Price", compute='compute_inventory_valuation_cost_price')
    move_ids = fields.One2many('stock.move', 'product_remove_id', string='Stock Moves')
    route_id = fields.Many2one('stock.location.route', string='Route', domain=[('sale_selectable', '=', True)],
                               ondelete='restrict', check_company=True)

    @api.onchange('location_id', 'product_id', 'quantity')
    def onchange_location_id(self):
        # TDE FIXME: should'nt we use context / location ?
        if self.location_id and self.product_id:
            # availability = self.product_id.product_variant_id._product_available()
            # self.availability = availability[self.product_id.product_variant_id.id]['qty_available']
            total_availability = self.env['stock.quant']._get_available_quantity(self.product_id,
                                                                                 self.location_id, strict=True)
            self.availability = total_availability
            self.remaining_qty = self.quantity - total_availability
            self.product_uom = self.product_id.uom_id

    @api.depends('product_id', 'availability', 'quantity')
    def compute_inventory_valuation_cost_price(self):
        for product in self:
            value = 0.0
            quantity = 0.0
            remaining_qty = 0.0
            stock_valuation_object = self.env['stock.valuation.layer'].search([
                ('product_id', '=', product.product_id.id)
            ])
            for stock in stock_valuation_object:
                quantity += stock.quantity
                value += stock.value
                remaining_qty += stock.remaining_qty
            if product.availability and quantity:
                product.cost_price = (value / quantity) * product.quantity
            else:
                product.cost_price = 0.0

    @api.depends('product_id', 'cost_price', 'quantity')
    def compute_unit_price(self):
        for product in self:
            if product.quantity:
                product.unit_price = product.cost_price / product.quantity
            else:
                product.unit_price = 0.0

    @api.constrains('quantity')
    def quantity_percentage_not_minus(self):
        for product in self:
            if product.quantity < 0:
                raise ValidationError('Please enter a positive number in Quantity')

    def _get_procurement_group(self):
        return self.conversion_id.procurement_group_ids

    def _prepare_procurement_group_vals(self):
        return {
            'name': self.conversion_id.name,
            'move_type': 'direct',
            'conversion_id': self.conversion_id.id,
            'product_remove_id': self.id,
            'partner_id': self.conversion_id.partner_shipping_id.id,
        }

    def _get_qty_procurement(self, previous_product_uom_qty=False):
        self.ensure_one()
        qty = 0.0
        outgoing_moves, incoming_moves = self._get_outgoing_incoming_moves()
        for move in outgoing_moves:
            qty += move.product_uom._compute_quantity(move.product_uom_qty, self.product_uom, rounding_method='HALF-UP')
        for move in incoming_moves:
            qty -= move.product_uom._compute_quantity(move.product_uom_qty, self.product_uom, rounding_method='HALF-UP')
        return qty

    def _get_outgoing_incoming_moves(self):
        outgoing_moves = self.env['stock.move']
        incoming_moves = self.env['stock.move']

        for move in self.move_ids.filtered(
                lambda r: r.state != 'cancel' and not r.scrapped and self.product_id == r.product_id):
            if move.location_dest_id.usage == "customer":
                if not move.origin_returned_move_id or (move.origin_returned_move_id and move.to_refund):
                    outgoing_moves |= move
            elif move.location_dest_id.usage != "customer" and move.to_refund:
                incoming_moves |= move

        return outgoing_moves, incoming_moves

    def _prepare_procurement_values(self, group_id=False):
        """ Prepare specific key for moves or other components that will be created from a stock rule
        comming from a sale order line. This method could be override in order to add other custom key that could
        be used in move/po creation.
        """
        # values = super(ProductRemove, self)._prepare_procurement_values(group_id)

        values = {}

        self.ensure_one()
        date_planned = self.conversion_id.conversion_date
        values.update({
            'group_id': group_id,
            'product_remove_id': self.id,
            'conversion_id': self.conversion_id.id,
            'date_planned': date_planned,
            'route_ids': self.product_id.route_ids,
            'warehouse_id': self.conversion_id.warehouse_id or False,
            'partner_id': self.conversion_id.partner_shipping_id.id,
            'company_id': self.conversion_id.company_id,
        })
        return values
