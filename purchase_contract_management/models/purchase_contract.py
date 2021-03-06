# -*- encoding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo import models, fields, api, exceptions, _


class PurchaseContract(models.Model):
    _name = 'purchase.contract'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Purchase Contract'
    _rec_name = 'name'
    _order = 'name DESC'

    name = fields.Char(string="Contract", required=True, copy=False,
                       default=lambda self: self.env['ir.sequence'].next_by_code('purchase.contract') or '/',
                       tracking=True)

    state = fields.Selection([('new', 'New'),
                              ('in_progress', 'IN Progress'),
                              ('cancel', 'Cancelled'),
                              ('partially_done', 'Partially Done & Close'),
                              ('done', 'Done'), ],
                             'Status', required=True, default='new',
                             copy=False, tracking=True)
    import_permit = fields.Char("Import Permit")
    vendor_id = fields.Many2one('res.partner', string="Vendor", required=True, domain="[('supplier_rank', '>', 0)]")
    contract_date = fields.Date("Contract Date", required=True)
    shipping_date = fields.Date("Start Shipping Date")
    end_shipping_date = fields.Date("End Shipping Date")
    payment_term = fields.Char("Payment Terms")
    variety = fields.Char("variety")
    containers_no = fields.Char("Containers No.")
    packages_id = fields.Many2one('stock.quant.package', string="Packages")
    packing_type = fields.Char(string="Packing type")
    product_id = fields.Many2one('product.product', string="Product",
                                 domain="[('contract','=',True)]", required=True)
    product_brand_origin = fields.Many2one('product.brand', string="Origin")
    contract_type_id = fields.Many2one('contract.type', string="Contract Type", required=True)
    contract_deliver_to_id = fields.Many2one('contract.deliver.to', string="Contract Deliver To")

    quantity = fields.Float(string="Quantity", required=True, default=1.0, tracking=True)
    ship_qty = fields.Float(string="Ship QTY", compute="_compute_ship_qty", store=True, tracking=True)
    close_reconcile_qty = fields.Float(string="Close Reconcile QTY", tracking=True)
    ship_remaining_qty = fields.Float(string="Ship Remaining QTY", compute="_compute_ship_remaining_qty", store=True,
                                      tracking=True)
    po_qty = fields.Float(string="PO QTY", compute="_compute_po_qty", store=True, tracking=True)
    po_remaining_qty = fields.Float(string="PO Remaining QTY", compute="_compute_po_remaining_qty", store=True,
                                    tracking=True)

    unit_price = fields.Float(string="Unit Price", required=True, default=1.0, tracking=True)
    currency_id = fields.Many2one('res.currency', string="Currency", required=True, tracking=True,
                                  default=lambda self: self.env.company.currency_id)
    amount = fields.Monetary('Amount', compute='_compute_amount', store=True, tracking=True)
    total_advance_payment = fields.Monetary('Total Advance Payment', compute='_compute_total_advance_payment',
                                            store=True, tracking=True)
    net_amount = fields.Monetary('Net Amount', compute='_compute_net_amount', store=True, tracking=True)

    purchase_contract_line_ids = fields.One2many('purchase.contract.line', 'contract_id',
                                                 string='Ship Lines', copy=False)
    contract_operation_line_ids = fields.One2many('contract.operation.line', 'contract_id',
                                                  string='Contract Operation', copy=False)
    ship_cost_line_ids = fields.One2many('ship.cost.line', 'contract_id',
                                         string='Ship Cost', copy=False)

    order_count = fields.Integer(compute='compute_purchase_order_count')
    purchase_line_ids = fields.One2many('purchase.order.line', 'contract_id', string='PurchaseLine',
                                        domain="[('state', 'in', ['draft','sent','purchase','done'])]")

    account_payment_ids = fields.One2many('account.payment', 'contract_id', string="Advanced Payment",
                                          domain="[('state', 'in', ['draft','sent','posted','reconciled'])]")
    amount_residual = fields.Float('Residual amount', readonly=True, compute="_get_amount")
    account_payment_count = fields.Integer(compute='compute_account_payment_count')
    account_move_ids = fields.One2many('account.move', 'contract_id', string="Vendor Bills",
                                       domain="[('type', '=', 'in_invoice'),('state', 'in', ['draft','posted'])]")
    account_move_count = fields.Integer(compute='compute_account_move_count')

    sale_contract_ids = fields.One2many('sale.contract', 'purchase_contract_id', string="Sale Contract", copy=False)
    purchase_contract_count_sale = fields.Integer(compute='compute_sale_contract_count')

    @api.depends('purchase_contract_line_ids.quantity', 'purchase_contract_line_ids')
    def _compute_ship_qty(self):
        for contract in self:
            total_qty = []
            for rec in contract.purchase_contract_line_ids:
                total_qty.append(rec.quantity)
            contract.ship_qty = sum(total_qty)

    @api.depends('ship_qty', 'quantity', 'close_reconcile_qty')
    def _compute_ship_remaining_qty(self):
        for contract in self:
            contract.ship_remaining_qty = contract.quantity - contract.ship_qty - contract.close_reconcile_qty

    @api.depends('purchase_line_ids.product_qty', 'purchase_line_ids')
    def _compute_po_qty(self):
        for contract in self:
            total_po_qty = []
            for rec in contract.purchase_line_ids:
                if rec.state in ['purchase', 'done']:
                    total_po_qty.append(rec.product_qty)
            contract.po_qty = sum(total_po_qty)

    @api.depends('po_qty', 'quantity')
    def _compute_po_remaining_qty(self):
        for contract in self:
            contract.po_remaining_qty = contract.quantity - contract.po_qty

    @api.depends('unit_price', 'quantity')
    def _compute_amount(self):
        for contract in self:
            contract.amount = contract.unit_price * contract.quantity

    @api.depends('account_payment_ids.amount', 'account_payment_ids')
    def _compute_total_advance_payment(self):
        for contract in self:
            total_payment = []
            for rec in contract.account_payment_ids:
                if rec.state not in ['draft', 'cancel']:
                    total_payment.append(rec.amount)
            contract.total_advance_payment = sum(total_payment)

    @api.depends('amount', 'total_advance_payment')
    def _compute_net_amount(self):
        for contract in self:
            contract.net_amount = contract.amount - contract.total_advance_payment

    def compute_purchase_order_count(self):
        self.order_count = self.env['purchase.order'].search_count(
            [('contract_id', 'in', self.ids)])

    def compute_account_payment_count(self):
        self.account_payment_count = self.env['account.payment'].search_count(
            [('contract_id', 'in', self.ids)])

    def compute_account_move_count(self):
        self.account_move_count = self.env['account.move'].search_count(
            [('contract_id', 'in', self.ids), ('type', '=', 'in_invoice')])

    def compute_sale_contract_count(self):
        if len(self.sale_contract_ids) > 0:
            self.purchase_contract_count_sale = self.env['sale.contract'].search_count(
                [('purchase_contract_id', 'in', self.ids)])
        else:
            self.purchase_contract_count_sale = 0.0

    def action_purchase_order(self):
        [action] = self.env.ref('purchase.purchase_rfq').read()
        action['domain'] = [('contract_id', 'in', self.ids)]
        return action

    def action_sale_contract(self):
        ship_lines = []
        [action] = self.env.ref('sale_contract_management.sale_contract_action').read()
        action['domain'] = [('purchase_contract_id', 'in', self.ids)]
        for line in self.purchase_contract_line_ids:
            ship_lines.append([0, 0, {
                # 'name': line.name,
                'product_id': line.product_id.id,
                'picking_type_id': line.picking_type_id.id,
                'invoice_no': line.invoice_no,
                'invoice_date': line.invoice_date,
                'quantity': line.quantity,
                'customs_no': line.customs_no,
                'customs_date': line.customs_date,
                'bl_no': line.bl_no,
                'bl_date': line.bl_date,
                'vessel_date': line.vessel_date,
                'vessel_name': line.vessel_name,
                'pol': line.pol,
                'pod': line.pod,
                'purchase_contract_line_id': line.id,
            }])
        action['context'] = {
            'default_product_id': self.product_id.id,
            'default_product_brand_origin': self.product_brand_origin.id,
            'default_shipping_date': self.shipping_date,
            'default_end_shipping_date': self.end_shipping_date,
            'default_contract_type_id': self.contract_type_id.id,
            'default_purchase_contract_id': self.id,
            'default_import_permit': self.import_permit,
            'default_contract_date': self.contract_date,
            'default_payment_term': self.payment_term,
            'default_variety': self.variety,
            'default_containers_no': self.containers_no,
            'default_packages_id': self.packages_id.id,
            'default_packing_type': self.packing_type,
            'default_purchase_sale_contract': True,
            'default_sale_contract_line_ids': [ship for ship in ship_lines]
        }
        return action

    def _get_amount(self):
        advance_amount = 0.0
        for line in self.account_payment_ids:
            if line.state != 'draft':
                advance_amount += line.amount
        self.amount_residual = self.amount_total - advance_amount

    def action_vendor_payment(self):
        [action] = self.env.ref('account.action_account_payments_payable').read()
        action['domain'] = [('contract_id', 'in', self.ids)]
        return action

    def action_account_move(self):
        [action] = self.env.ref('account.action_move_in_invoice_type').read()
        action['domain'] = [('contract_id', 'in', self.ids), ('type', '=', 'in_invoice')]
        return action

    def btn_advance_payment(self):
        ctx = {'default_payment_type': 'outbound',
               'default_partner_id': self.vendor_id.id,
               'default_partner_type': 'supplier',
               'search_default_outbound_filter': 1,
               'res_partner_search_mode': 'supplier',
               'default_currency_id': self.currency_id.id,
               'default_payment_date': self.contract_date,
               'default_contract_id': self.id,
               'default_communication': self.name,
               'default_payment_method_id': self.env.ref('account.account_payment_method_manual_out').id,
               'active_ids': [],
               'active_model': self._name,
               'active_id': self.id,
               'default_check_contract_payment': True,
               }

        return {'name': _("Advance Payment"),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'account.payment',
                'target': 'new',
                'view_id': self.env.ref(
                    'purchase_contract_management.view_contract_advance_account_payment_form').id,
                'context': ctx}

    @api.constrains('contract_date', 'shipping_date')
    def _check_contract_shipping_date(self):
        for contract in self:
            if contract.contract_date < contract.create_date.date():
                raise ValidationError(_('Contract date should not accept date before creation date.'))
            if contract.shipping_date:
                if contract.contract_date > contract.shipping_date:
                    raise ValidationError(_('Shipping date should not be date before contract date.'))

    @api.constrains('product_id')
    def _constrains_product_id(self):
        for contract in self:
            if contract.product_id != False:
                if contract.product_id.contract != True:
                    raise ValidationError(_('You should select products with contract checkbox only.'))

    @api.constrains('quantity', 'close_reconcile_qty', 'unit_price')
    def quantity_not_minus(self):
        for contract in self:
            if contract.quantity < 0:
                raise ValidationError('Please enter a positive number in Quantity')

            if contract.close_reconcile_qty < 0:
                raise ValidationError('Please enter a positive number in Close Reconcile QTY')

            if contract.unit_price < 0:
                raise ValidationError('Please enter a positive number in Unit Price')

    def unlink(self):
        for line in self:
            if len(line.purchase_contract_line_ids) > 0 or len(line.contract_operation_line_ids) > 0 or len(
                    line.ship_cost_line_ids) > 0 or len(line.purchase_line_ids) > 0 or len(
                line.account_payment_ids) > 0 or len(line.account_move_ids) > 0:
                raise ValidationError(
                    'You cannot delete this Purchase Contract because it related with transactions created.')
        return super(PurchaseContract, self).unlink()


class SaleContract(models.Model):
    _inherit = 'sale.contract'

    purchase_contract_id = fields.Many2one('purchase.contract', string="Purchase Contract", readonly=True)
    contract_type_id = fields.Many2one('contract.type', string="Contract Type", readonly=True,
                                       states={'new': [('readonly', False)]}, required=True)
    end_shipping_date = fields.Date("End Shipping Date", readonly=True,
                                    states={'new': [('readonly', False)]})
    contract_deliver_to_id = fields.Many2one('contract.deliver.to', string="Contract Deliver To", readonly=True,
                                             states={'new': [('readonly', False)]})
    spacial_unit_price = fields.Float(string="Spacial Unit Price", required=True, default=1.0, tracking=True,
                                      readonly=True,
                                      states={'new': [('readonly', False)]})
    spacial_currency_id = fields.Many2one('res.currency', string="Spatial Currency", required=True, tracking=True,
                                          readonly=True,
                                          states={'new': [('readonly', False)]},
                                          default=lambda self: self.env.company.currency_id)
    spacial_amount = fields.Monetary('Spacial Amount', compute='_compute_spacial_amount', store=True, tracking=True)
    purchase_sale_contract = fields.Boolean('Purchase Sale Contract')
    pricelist_currency_id = fields.Many2one('res.currency', related='pricelist_id.currency_id', readonly=True)
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist', required=True, help='Pricelist when added',
                                   default=lambda self: self.env['product.pricelist'].search(
                                       [('company_id', 'in', [self.env.company.id, False])], limit=1).id)
    spacial_pricelist_currency_id = fields.Many2one('res.currency', related='spacial_pricelist_id.currency_id', readonly=True)
    spacial_pricelist_id = fields.Many2one('product.pricelist', string='Pricelist', help='Pricelist when added',
                                           required=True, default=lambda self: self.env['product.pricelist'].search(
            [('company_id', 'in', [self.env.company.id, False])], limit=1).id)

    @api.onchange('customer_id')
    def onchange_customer_id_changes(self):
        if self.customer_id:
            self.pricelist_id = self.customer_id.property_product_pricelist
            self.spacial_pricelist_id = self.customer_id.property_product_pricelist

    @api.depends('spacial_unit_price', 'quantity')
    def _compute_spacial_amount(self):
        for contract in self:
            contract.spacial_amount = contract.spacial_unit_price * contract.quantity


class SaleContractLine(models.Model):
    _inherit = 'sale.contract.line'

    vessel_name = fields.Char("Vessel Name")
    container_size_id = fields.Many2one('container.size', string="Container Size")
    purchase_contract_line_id = fields.Many2one('purchase.contract.line', string="Purchase Ship Line",
                                                readonly=True)
