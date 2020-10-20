# -*- encoding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo import models, fields, api, exceptions, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare


class ProductConversion(models.Model):
    _name = 'product.conversion'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Product Conversion'
    _rec_name = 'name'
    _order = 'name DESC'

    name = fields.Char(string="Product Conversion", required=True, copy=False,
                       default=lambda self: self.env['ir.sequence'].next_by_code('product.conversion') or '/',
                       tracking=True, readonly=True,
                       states={'draft': [('readonly', False)]})

    state = fields.Selection([('draft', 'Draft'),
                              ('assigned', 'Ready'),
                              ('cancel', 'Cancelled'),
                              ('done', 'Done')],
                             'Status', required=True, default='draft',
                             copy=False, tracking=True)

    conversion_date = fields.Datetime("Date & Time", default=fields.Datetime.now, readonly=True,
                                      states={'draft': [('readonly', False)]}, tracking=True)

    product_to_remove_ids = fields.One2many('product.remove', 'conversion_id', string='Remove', readonly=True,
                                            states={'draft': [('readonly', False)]})

    product_to_add_ids = fields.One2many('product.add', 'conversion_id', string="Add", readonly=True,
                                         states={'draft': [('readonly', False)]})
    stock_picking_ids = fields.One2many('stock.picking', 'conversion_id', string="Picking", readonly=True,
                                        states={'draft': [('readonly', False)]})

    stock_picking_count = fields.Integer(compute='compute_stock_picking_count', string="#picking", copy=False)
    check_availability = fields.Boolean(copy=False)
    procurement_group_id = fields.Many2one('procurement.group', 'Procurement Group Of Remove Products', copy=False)
    procurement_group_id_in = fields.Many2one('procurement.group', 'Procurement Group Of Add Products', copy=False)
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True,
                                 default=lambda self: self.env.company, readonly=True,
                                 states={'draft': [('readonly', False)], 'assigned': [('readonly', False)]})

    @api.model
    def _default_warehouse_id(self):
        company = self.env.company.id
        warehouse_ids = self.env['stock.warehouse'].search([('company_id', '=', company)], limit=1)
        return warehouse_ids

    warehouse_id = fields.Many2one(
        'stock.warehouse', string='Warehouse',
        required=True, readonly=True, states={'draft': [('readonly', False)], 'assigned': [('readonly', False)]},
        default=_default_warehouse_id, check_company=True)
    partner_shipping_id = fields.Many2one(
        'res.partner', string='Delivery Address', readonly=True, required=True,
        states={'draft': [('readonly', False)], 'assigned': [('readonly', False)]},
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", )

    @api.model
    def _get_picking_type(self, company_id):
        picking_type = self.env['stock.picking.type'].search(
            [('code', '=', 'incoming'), ('warehouse_id.company_id', '=', company_id)])
        if not picking_type:
            picking_type = self.env['stock.picking.type'].search(
                [('code', '=', 'incoming'), ('warehouse_id', '=', False)])
        return picking_type[:1]

    @api.model
    def _default_picking_type(self):
        return self._get_picking_type(self.env.context.get('company_id') or self.env.company.id)

    picking_type_id = fields.Many2one('stock.picking.type', 'Deliver To',
                                      required=True, default=_default_picking_type,
                                      domain="['|', ('warehouse_id', '=', False), ('warehouse_id.company_id', '=', company_id)]",
                                      help="This will determine operation type of incoming shipment", readonly=True,
                                      states={'draft': [('readonly', False)], 'assigned': [('readonly', False)]})

    @api.depends('stock_picking_ids')
    def compute_stock_picking_count(self):
        self.stock_picking_count = self.env['stock.picking'].search_count(
            [('conversion_id', 'in', self.ids)])

    def action_stock_picking(self):
        [action] = self.env.ref('stock.action_picking_tree_all').read()
        action['domain'] = [('conversion_id', 'in', self.ids)]
        return action

    def check_quants_availability(self):
        for record in self.product_to_remove_ids:
            if record.location_id:
                domain_quants = [
                    ('product_id', '=', record.product_tmp_id.product_variant_id.id),
                    ('location_id', '=', record.location_id.id)
                ]
                quants = self.env['stock.quant'].read_group(
                    domain_quants, ['product_id', 'location_id', 'quantity'],
                    ['location_id', 'product_id'], orderby='quantity ASC')
                total_qty = quants and quants[0].get('quantity') or 0.0
                if total_qty == 0.0:
                    raise UserError(
                        _("Product %s not have availability in %s. \n\n"
                          "Please check your inventory, receipts or deliveries"
                          % (record.product_tmp_id.product_variant_id.name, record.location_id.name)))
                elif record.quantity > total_qty:
                    raise UserError(
                        _("Product %s only has %s %s available in %s."
                          % (record.product_tmp_id.product_variant_id.name, total_qty,
                             record.product_uom.name, record.location_id.name)))
                else:
                    self.check_availability = True
                    self.write({'state': 'assigned'})
            else:
                raise UserError(
                    _("Please Select a Inventory Locations in Product To Remove Lines"))
        return True

    def action_confirm(self):
        self.write({'state': 'done'})
        previous_product_uom_qty = False
        stock_picking = self.env['stock.picking']
        for order in self.product_to_add_ids:
            if any([ptype in ['product', 'consu'] for ptype in order.mapped('product_id.type')]):
                pickings = self.stock_picking_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
                if not pickings:
                    res = order._prepare_picking()
                    picking = stock_picking.create(res)
                else:
                    picking = pickings[0]
                moves = order._create_stock_moves(picking)
                moves = moves.filtered(lambda x: x.state not in ('done', 'cancel'))._action_confirm()
                seq = 0
                for move in sorted(moves, key=lambda move: move.date_expected):
                    seq += 5
                    move.sequence = seq
                moves._action_assign()
                picking.message_post_with_view('mail.message_origin_link',
                                               values={'self': picking, 'origin': order},
                                               subtype_id=self.env.ref('mail.mt_note').id)
        """
        Launch procurement group run method with required/custom fields genrated by a
        Product To Remove. procurement group will launch '_run_pull', '_run_buy' or '_run_manufacture'
        depending on the Product To Remove product rule.
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        procurements = []
        for line in self.product_to_remove_ids:
            if not line.product_id.type in ('consu', 'product'):
                continue
            qty = line._get_qty_procurement(previous_product_uom_qty)
            if float_compare(qty, line.quantity, precision_digits=precision) >= 0:
                continue
            group_id = line._get_procurement_group()
            if not group_id:
                group_id = self.env['procurement.group'].create(line._prepare_procurement_group_vals())
                line.conversion_id.procurement_group_id = group_id
            values = line._prepare_procurement_values(group_id=group_id)
            product_qty = line.quantity - qty

            line_uom = line.product_uom
            quant_uom = line.product_id.uom_id
            product_qty, procurement_uom = line_uom._adjust_uom_quantities(product_qty, quant_uom)
            procurements.append(self.env['procurement.group'].Procurement(
                line.product_id, product_qty, procurement_uom,
                line.conversion_id.partner_shipping_id.property_stock_customer,
                line.name, line.conversion_id.name, line.conversion_id.company_id, values))
        if procurements:
            self.env['procurement.group'].run(procurements)

        return True

    def action_cancel(self):
        self.write({'state': 'cancel'})
