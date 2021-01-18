# -*- encoding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo import models, fields, api, exceptions, _


class SaleContractLine(models.Model):
    _name = 'sale.contract.line'
    _description = 'Sale Contract Lines'
    _rec_name = 'name'
    _order = 'name DESC'

    name = fields.Char(string="Shipping Line", required=True, readonly=True, copy=False, default='/')
    sale_contract_id = fields.Many2one('sale.contract', string="sale Contract")
    customer_id = fields.Many2one('res.partner', related='sale_contract_id.customer_id', string='Customer',
                                  readonly=True,
                                  store=True)
    currency_id = fields.Many2one(related='sale_contract_id.currency_id', store=True, string='Currency', readonly=True)
    contract_date = fields.Date(related='sale_contract_id.contract_date', store=True, string='Contract Date',
                                readonly=True)

    product_id = fields.Many2one('product.product', related='sale_contract_id.product_id',
                                 string="Product", store=True)
    invoice_no = fields.Char("Invoice No.")
    invoice_date = fields.Date("Invoice Date")
    customs_no = fields.Char("Customs No.")
    customs_date = fields.Date("Customs Date")
    quantity = fields.Float(string="Quantity", default=1.0)
    arrival_date = fields.Date("Arrival Date")
    bl_no = fields.Char("BL No.")
    bl_date = fields.Date("BL Date/ETS")
    vessel_date = fields.Date("Vessel Date/ETS")
    pol = fields.Char("POL")
    pod = fields.Char("POD")
    sale_created = fields.Boolean()
    sale_id = fields.Many2one('sale.order', string='Sale Order')

    @api.model
    def create(self, vals):
        if not vals.get('name') or vals['name'] == _('/'):
            vals['name'] = self.env['ir.sequence'].next_by_code('sale.contract.line') or '/'
        return super(SaleContractLine, self).create(vals)

    @api.model
    def _default_picking_type(self):
        type_obj = self.env["stock.picking.type"]
        company_id = self.env.context.get("company_id") or self.env.company.id
        types = type_obj.search(
            [("code", "=", "incoming"), ("warehouse_id.company_id", "=", company_id)]
        )
        if not types:
            types = type_obj.search(
                [("code", "=", "incoming"), ("warehouse_id", "=", False)]
            )
        return types[:1]

    picking_type_id = fields.Many2one(
        comodel_name="stock.picking.type",
        string="Picking Type",
        required=True,
        default=_default_picking_type,
    )

    def create_sale_order(self):
        self.sale_created = True
        company = self.env.company.id
        # product_product_obj = self.env['product.product'].search(
        #     [('product_tmpl_id', '=', self.product_template_id.id)])
        obj_sale = self.env['sale.order'].create({
            'partner_id': self.customer_id.id,
            'currency_id': self.currency_id.id,
            'date_order': self.contract_date,
            'sale_contract_id_line': self.id,
            'sale_contract_id': self.sale_contract_id.id,
            'warehouse_id': self.env['stock.warehouse'].search([('company_id', '=', company)], limit=1).id,
            'order_line': [(0, 0, ope) for ope in [{
                'name': self.product_id.name, 'product_id': self.product_id.id,
                'product_uom_qty': self.quantity,
                'currency_id': self.currency_id.id,
                'product_uom': self.product_id.uom_id.id, 'price_unit': self.sale_contract_id.unit_price,
                'sale_analytic_account_id': self.product_id.gio_analytic_account.id
            }]],
        })
        # obj_sale.button_confirm()
        self.sale_id = obj_sale.id
        self.sale_contract_id.write({'sale_line_ids': [(4, so_line.id) for so_line in obj_sale.order_line]})

    def unlink(self):
        for line in self:
            if line.sale_id:
                if line.sale_created == True:
                    raise ValidationError(
                        'You cannot delete this sale contract line because it related with SO created.')
        return super(SaleContractLine, self).unlink()

    @api.constrains('quantity')
    def quantity_not_minus(self):
        for line in self:
            if line.quantity < 0:
                raise ValidationError('Please enter a positive number in Quantity')
