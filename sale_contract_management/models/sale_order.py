from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sale_contract_id = fields.Many2one('sale.contract', string="Sale Contract", readonly=True,
                                       states={'draft': [('readonly', False)]}, )
    sale_contract_id_line = fields.Many2one('sale.contract.line', string="Sale Contract Line",
                                            states={'draft': [('readonly', False)]},
                                            readonly=True)

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        res = super(SaleOrder, self).onchange_partner_id()
        if self.sale_contract_id:
            self.pricelist_id = self.sale_contract_id.pricelist_id.id
        return res

    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        for rec in self:
            res['sale_contract_id'] = rec.sale_contract_id.id
            res['check_invoice'] = True
        return res

    def action_cancel(self):
        res = super(SaleOrder, self).action_cancel()
        all_qty = []
        for rec in self:
            # rec.sale_contract_id_line.sale_created = False
            for line in rec.order_line:
                all_qty.append(line.product_uom_qty)
            # rec.sale_contract_id.ship_qty -= sum(all_qty)
            rec.sale_contract_id.so_qty -= sum(all_qty)
        return res

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        all_qty = []
        for rec in self:
            for line in rec.order_line:
                all_qty.append(line.product_uom_qty)
            rec.sale_contract_id.so_qty += sum(all_qty)
        return res

    # doaa added
    def btn_advance_payment(self):
        cus_ctx = {'default_payment_type': 'inbound',
                   'default_partner_id': self.partner_id.id,
                   'default_partner_type': 'customer',
                   'search_default_inbound_filter': 1,
                   'res_partner_search_mode': 'customer',
                   'default_currency_id': self.currency_id.id,
                   'default_sale_contract_id': self.sale_contract_id.id,
                   'default_sale_id': self.id,
                   'default_communication': self.name,
                   'active_ids': [],
                   'active_model': self._name,
                   'active_id': self.id,
                   'default_sale_check_contract_payment': True,
                   }

        ctx = self._context.copy()
        ctx.update(cus_ctx)
        return {
            'name': _('Advance Payment'),
            'res_model': 'account.payment',
            'view_mode': 'form',
            'view_id': self.env.ref('eq_sale_advance_payment.view_sale_advance_account_payment_form').id,
            'target': 'new',
            'type': 'ir.actions.act_window',
            'context': ctx
        }


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    sale_contract_id = fields.Many2one('sale.contract', string="Sale Contract", related='order_id.sale_contract_id',
                                       readonly=True, store=True)
    sale_contract_id_line = fields.Many2one('sale.contract.line', related='order_id.sale_contract_id_line',
                                            string="Sale Contract Line"
                                            , readonly=True, store=True)
    payment_to_link = fields.Float(sring="Payment To Link")
    account_payment_ids = fields.Many2many('account.payment', string="Payments", compute='compute_account_payment_ids')
    account_payment_id = fields.Many2one('account.payment', string="Payments")

    @api.depends('order_id.adv_payment_ids', 'sale_contract_id.account_payment_ids')
    def compute_account_payment_ids(self):
        for so_line in self:
            payments_obj = self.env['account.payment'].search([('partner_id', '=', so_line.order_partner_id.id)])
            payments = []
            # for rec in so_line.order_id.account_payment_ids:
            #     payments.append(rec.id)
            for pay in payments_obj:
                payments.append(pay.id)
            so_line.account_payment_ids = [(6, 0, payments)]
