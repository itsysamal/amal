# -*- encoding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo import models, fields, api, exceptions, _


class PurchaseContractLine(models.Model):
    _name = 'purchase.contract.line'
    _description = 'Purchase Contract Lines'
    _rec_name = 'name'
    _order = 'name DESC'

    name = fields.Char(string="Shipping Line", required=True, readonly=True, copy=False, default='/')
    contract_id = fields.Many2one('purchase.contract', string="Purchase Contract")
    vendor_id = fields.Many2one('res.partner', related='contract_id.vendor_id', string='Vendor', readonly=True,
                                store=True)
    currency_id = fields.Many2one(related='contract_id.currency_id', store=True, string='Currency', readonly=True)
    contract_date = fields.Date(related='contract_id.contract_date', store=True, string='Contract Date', readonly=True)

    product_template_id = fields.Many2one('product.template', related='contract_id.product_template_id',
                                          string="Product Template", store=True)
    invoice_no = fields.Char("Invoice No.")
    invoice_date = fields.Date("Invoice Date")
    customs_no = fields.Char("Customs No.")
    customs_date = fields.Date("Customs Date")
    quantity = fields.Integer(string="Quantity", default=1.0)
    arrival_date = fields.Date("Arrival Date")
    bl_no = fields.Char("BL No.")
    bl_date = fields.Date("BL Date/ETS")
    vessel_date = fields.Date("Vessel Date/ETS")
    pol = fields.Date("POL")
    pod = fields.Date("POD")
    purchase_created = fields.Boolean()
    purchase_id = fields.Many2one('purchase.order', string='Purchase Order')

    @api.model
    def create(self, vals):
        if not vals.get('name') or vals['name'] == _('/'):
            vals['name'] = self.env['ir.sequence'].next_by_code('purchase.contract.line') or '/'
        return super(PurchaseContractLine, self).create(vals)

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

    def create_purchase_order(self):
        self.purchase_created = True
        product_product_obj = self.env['product.product'].search(
            [('product_tmpl_id', '=', self.product_template_id.id)])
        obj_purchase = self.env['purchase.order'].create({
            'partner_id': self.vendor_id.id,
            'currency_id': self.currency_id.id,
            'date_order': self.contract_date,
            'purchase_contract_id_line': self.id,
            'contract_id': self.contract_id.id,
            'picking_type_id': self.picking_type_id.id,
            'order_line': [(0, 0, ope) for ope in [{
                'name': product_product_obj.name, 'product_id': product_product_obj.id,
                'product_qty': self.quantity,
                'product_uom': product_product_obj.uom_id.id, 'price_unit': self.contract_id.unit_price,
                'date_planned': fields.Datetime.now()
            }]],
        })
        # obj_purchase.button_confirm()
        self.purchase_id = obj_purchase.id
        self.contract_id.write({'purchase_line_ids': [(4, po_line.id) for po_line in obj_purchase.order_line]})

    def unlink(self):
        for line in self:
            if line.purchase_id:
                if line.purchase_created == True:
                    raise ValidationError(
                        'You cannot delete this purchase contract line because it related with PO created.')
        return super(PurchaseContractLine, self).unlink()

    @api.constrains('quantity')
    def quantity_not_minus(self):
        for line in self:
            if line.quantity < 0:
                raise ValidationError('Please enter a positive number in Quantity')
