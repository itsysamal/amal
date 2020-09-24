from odoo import api, fields, models, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    contract_id = fields.Many2one('purchase.contract', string="Purchase Contract", readonly=True)
    purchase_contract_id_line = fields.Many2one('purchase.contract.line', string="Purchase Contract Line",
                                                readonly=True)

    def action_view_invoice(self):
        res = super(PurchaseOrder, self).action_view_invoice()
        for rec in self:
            res['context']['default_contract_id'] = rec.contract_id.id
        return res

    def button_cancel(self):
        res = super(PurchaseOrder, self).button_cancel()
        all_qty=[]
        for rec in self:
            # rec.purchase_contract_id_line.purchase_created = False
            for line in rec.order_line:
                all_qty.append(line.product_qty)
            rec.contract_id.ship_qty -= sum(all_qty)
            rec.contract_id.po_qty -= sum(all_qty)
        return res

    # doaa added
    def btn_advance_payment(self):
        date = ''
        if self.date_approve:
            date = self.date_approve
        if self.date_order:
            date = self.date_order
        ctx = {'default_payment_type': 'outbound',
               'default_partner_id': self.partner_id.id,
               'default_partner_type': 'supplier',
               'search_default_outbound_filter': 1,
               'res_partner_search_mode': 'supplier',
               'default_currency_id': self.currency_id.id,
               'default_payment_date': date,
               'default_contract_id': self.contract_id.id,
               'default_purchase_id': self.id,
               'default_communication': self.name,
               'default_payment_method_id': self.env.ref('account.account_payment_method_manual_out').id,
               'active_ids': [],
               'active_model': self._name,
               'active_id': self.id,
               }

        return {'name': _("Advance Payment"),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'account.payment',
                'target': 'new',
                'view_id': self.env.ref(
                    'xs_purchase_advance_payment.view_purchase_advance_account_payment_form').id,
                'context': ctx}


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    contract_id = fields.Many2one('purchase.contract', string="Purchase Contract", readonly=True)
    purchase_contract_id_line = fields.Many2one('purchase.contract.line', string="Purchase Contract Line",
                                                readonly=True)
