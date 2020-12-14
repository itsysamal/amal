# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare


class ProductAdd(models.Model):
    _name = 'product.add'
    _description = 'Product To Add'
    _rec_name = 'name'
    _order = 'name DESC'

    name = fields.Char(string="Name", required=True, copy=False)
    conversion_id = fields.Many2one('product.conversion', string="Product Conversion")
    product_id = fields.Many2one('product.product', string="Product", required=True)
    product_tmp_id = fields.Many2one('product.template', related='product_id.product_tmpl_id',
                                     string="Product Template", store=True)
    location_id = fields.Many2one('stock.location', string="Inventory Locations", required=True)
    lot_id = fields.Many2one('stock.production.lot', string="Lot /Serial")
    analytic_account_id = fields.Many2one("account.analytic.account", string='Analytic Account')
    analytic_tag_ids = fields.Many2one("account.analytic.tag", string='Analytic Tags')
    branch_id = fields.Many2one('res.branch', string='Branch')
    quantity = fields.Float(string="Quantity", default=1.0)
    product_uom = fields.Many2one('uom.uom', string='UOM',
                                  domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=True)

    percentage = fields.Integer(string="%")
    fixed_percentage = fields.Selection([('fixed', 'Fixed'),
                                         ('percentage', 'Percentage')],
                                        'Cost Type', required=True,
                                        copy=False, tracking=True)
    editable_unit_price = fields.Float(string="Fixed Unit Price")
    unit_price = fields.Float(string="Unit Price", compute='compute_unit_price')
    cost_price = fields.Float(string="Cost Price", compute='compute_cost_price')
    remaining_qty = fields.Float(string="Remaining quantity")
    availability = fields.Float(string="Available")
    allocate_expense = fields.Float(string="Allocate Expense", compute='compute_allocate_expense')

    remaining_cost = fields.Float(string="Remaining Cost", compute='compute_remaining_cost')
    new_cost_price_edit = fields.Float(string="Final Cost", compute='compute_final_cost')
    final_item_cost = fields.Float(string="Final Item Cost", compute='compute_final_item_cost')
    new_cost_price = fields.Float(string="Final Item Cost",
                                  compute='compute_inventory_valuation_new_cost_price')

    move_ids = fields.One2many('stock.move', 'product_add_id', string='Stock Moves')
    move_dest_ids = fields.One2many('stock.move', 'created_purchase_line_id', 'Downstream Moves')

    date_planned = fields.Datetime(string='Scheduled Date', index=True, required=True)

    @api.depends('product_id', 'unit_price', 'quantity','editable_unit_price')
    def compute_cost_price(self):
        for product in self:
            if product.quantity and product.unit_price:
                product.cost_price = product.unit_price * product.quantity
            elif product.quantity and product.editable_unit_price:
                product.cost_price = product.editable_unit_price * product.quantity
            else:
                product.cost_price = 0.0

    @api.depends('cost_price', 'allocate_expense')
    def compute_final_cost(self):
        for product in self:
            if product.allocate_expense and product.cost_price:
                product.new_cost_price_edit = product.cost_price + product.allocate_expense
            else:
                product.new_cost_price_edit = 0.0

    @api.depends('new_cost_price_edit', 'quantity')
    def compute_final_item_cost(self):
        for product in self:
            if product.new_cost_price_edit and product.quantity:
                product.final_item_cost = product.new_cost_price_edit / product.quantity
            else:
                product.final_item_cost = 0.0

    @api.depends('product_id', 'quantity', 'percentage', 'conversion_id',
                 'conversion_id.product_to_remove_ids', 'conversion_id.product_to_remove_ids.cost_price','fixed_percentage')
    def compute_unit_price(self):
        for product in self:
            total_cost_of_remove = 0.0
            for remove in product.conversion_id.product_to_remove_ids:
                total_cost_of_remove += remove.cost_price
            if total_cost_of_remove and product.quantity and product.percentage and product.fixed_percentage == 'percentage':
                product.unit_price = (total_cost_of_remove * (product.percentage/100)) / product.quantity
            else:
                product.unit_price = 0.0

    @api.depends('conversion_id','cost_price',
                 'conversion_id.product_to_remove_ids', 'conversion_id.product_to_remove_ids.cost_price')
    def compute_remaining_cost(self):
        for product in self:
            total_cost_of_remove = 0.0
            for remove in product.conversion_id.product_to_remove_ids:
                total_cost_of_remove += remove.cost_price
            if total_cost_of_remove and product.cost_price:
                product.remaining_cost = product.cost_price - (total_cost_of_remove/2)
            else:
                product.remaining_cost = 0.0

    @api.depends('product_id', 'unit_price', 'conversion_id',
                 'conversion_id.product_expense_ids', 'conversion_id.product_expense_ids.quantity')
    def compute_allocate_expense(self):
        for product in self:
            total_unit_price = 0.0
            for remove in product.conversion_id.product_expense_ids:
                total_unit_price += remove.unit_price
            if total_unit_price and product.quantity:
                product.allocate_expense = total_unit_price * product.quantity
            else:
                product.allocate_expense = 0.0

    @api.onchange('location_id', 'product_id', 'quantity')
    def onchange_location_id(self):
        # TDE FIXME: should'nt we use context / location ?
        if self.location_id and self.product_id:
            total_availability = self.env['stock.quant']._get_available_quantity(self.product_id,
                                                                                 self.location_id, strict=True)
            self.availability = total_availability
            self.remaining_qty = self.quantity - total_availability
        if self.product_id:
            self.product_uom = self.product_id.uom_id
            self.analytic_account_id = self.product_id.gio_analytic_account
            self.analytic_tag_ids = self.product_id.gio_analytic_tag

    @api.constrains('quantity', 'percentage')
    def quantity_percentage_not_minus(self):
        for product in self:
            if product.quantity < 0:
                raise ValidationError('Please enter a positive number in Quantity')

            if product.percentage < 0:
                raise ValidationError('Please enter a positive number in Percentage')

    @api.depends('product_id', 'percentage', 'conversion_id', 'conversion_id.product_to_remove_ids', 'fixed_percentage',
                 'new_cost_price_edit')
    def compute_inventory_valuation_new_cost_price(self):
        for rec in self:
            total_cost_of_remove = 0.0
            for product in self.conversion_id.product_to_remove_ids:
                total_cost_of_remove += product.cost_price

            if total_cost_of_remove > 0 and rec.fixed_percentage == 'percentage':
                rec.new_cost_price = (total_cost_of_remove * rec.percentage) / 100
                rec.new_cost_price_edit = 0.0
            elif rec.fixed_percentage == 'fixed':
                rec.new_cost_price = rec.new_cost_price_edit
                rec.percentage = 0.0
            else:
                rec.new_cost_price = 0.0
                rec.new_cost_price_edit = 0.0

    def _get_destination_location(self):
        self.ensure_one()
        if self.conversion_id.partner_shipping_id:
            return self.conversion_id.partner_shipping_id.property_stock_customer.id
        return self.conversion_id.picking_type_id.default_location_dest_id.id

    @api.model
    def _prepare_picking(self):
        if not self.conversion_id.procurement_group_id_in:
            self.conversion_id.procurement_group_id_in = self.conversion_id.procurement_group_id_in.create({
                'name': self.conversion_id.name,
                'conversion_id': self.conversion_id.id,
                'partner_id': self.conversion_id.partner_shipping_id.id
            })
        if not self.conversion_id.partner_shipping_id.property_stock_supplier.id:
            raise UserError(
                _("You must set a Vendor Location for this partner %s") % self.conversion_id.partner_shipping_id.name)
        return {
            'picking_type_id': self.conversion_id.picking_type_id.id,
            'partner_id': self.conversion_id.partner_shipping_id.id,
            'user_id': False,
            'date': self.conversion_id.conversion_date,
            'origin': self.name,
            'location_dest_id': self.location_id.id,
            'location_id': self.conversion_id.partner_shipping_id.property_stock_supplier.id,
            'company_id': self.conversion_id.company_id.id,
        }

    def _get_stock_move_price_unit(self):
        self.ensure_one()
        line = self[0]
        price_unit = line.final_item_cost
        if line.product_uom.id != line.product_id.uom_id.id:
            price_unit *= line.product_uom.factor / line.product_id.uom_id.factor
        return price_unit

    def _prepare_stock_moves(self, picking):
        """ Prepare the stock moves data for one order line. This function returns a list of
        dictionary ready to be used in stock.move's create()
        """
        self.ensure_one()
        res = []
        if self.product_id.type not in ['product', 'consu']:
            return res
        qty = 0.0
        price_unit = self._get_stock_move_price_unit()
        for move in self.move_ids.filtered(
                lambda x: x.state != 'cancel' and not x.location_dest_id.usage == "supplier"):
            qty += move.product_uom._compute_quantity(move.product_uom_qty, self.product_uom, rounding_method='HALF-UP')
        template = {
            # truncate to 2000 to avoid triggering index limit error
            # TODO: remove index in master?
            'name': (self.name or '')[:2000],
            'product_id': self.product_id.id,
            'product_uom': self.product_uom.id,
            'date': self.conversion_id.conversion_date,
            'date_expected': self.date_planned,
            'location_id': self.conversion_id.partner_shipping_id.property_stock_supplier.id,
            # 'location_dest_id': self._get_destination_location(),
            'location_dest_id': self.location_id.id,
            'picking_id': picking.id,
            'partner_id': self.conversion_id.partner_shipping_id.id,
            'move_dest_ids': [(4, x) for x in self.move_dest_ids.ids],
            'state': 'draft',
            'product_add_id': self.id,
            'conversion_id': self.conversion_id.id,
            'company_id': self.conversion_id.company_id.id,
            'price_unit': price_unit,
            'picking_type_id': self.conversion_id.picking_type_id.id,
            'group_id': self.conversion_id.procurement_group_id_in.id,
            'origin': self.conversion_id.name,
            'analytic_account_id': self.analytic_account_id.id,
            'analytic_tag_ids': self.analytic_tag_ids.ids,
            # 'propagate_date': self.propagate_date,
            # 'propagate_date_minimum_delta': self.propagate_date_minimum_delta,
            'description_picking': self.product_id._get_description(self.conversion_id.picking_type_id),
            # 'propagate_cancel': self.propagate_cancel,
            'route_ids': self.conversion_id.picking_type_id.warehouse_id and [
                (6, 0, [x.id for x in self.conversion_id.picking_type_id.warehouse_id.route_ids])] or [],
            'warehouse_id': self.conversion_id.picking_type_id.warehouse_id.id,
        }
        diff_quantity = self.quantity - qty
        if float_compare(diff_quantity, 0.0, precision_rounding=self.product_uom.rounding) > 0:
            po_line_uom = self.product_uom
            quant_uom = self.product_id.uom_id
            product_uom_qty, product_uom = po_line_uom._adjust_uom_quantities(diff_quantity, quant_uom)
            template['product_uom_qty'] = product_uom_qty
            template['product_uom'] = product_uom.id
            res.append(template)
        return res

    def _create_stock_moves(self, picking):
        values = []
        for line in self:
            for val in line._prepare_stock_moves(picking):
                values.append(val)
        return self.env['stock.move'].create(values)
