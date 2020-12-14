from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo import models, fields, api, exceptions, _


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    contract_id = fields.Many2one('purchase.contract', string="Purchase Contract", readonly=True, store=True,
                                  states={'draft': [('readonly', False)]})
    create_in_state_contract = fields.Selection([('draft', 'Draft'),
                                                 ('confirm', 'Confirm')],
                                                default='draft',
                                                string="Payment Status")
    check_contract_payment = fields.Boolean()

    purchase_id = fields.Many2one('purchase.order', "Purchase",
                                  readonly=True, states={'draft': [('readonly', False)]})
    purchase_ids = fields.Many2many('purchase.order', string='Purchases', compute='compute_purchase_ids')

    @api.depends('contract_id.purchase_line_ids')
    def compute_purchase_ids(self):
        for contract in self:
            purchase = []
            for rec in contract.contract_id.purchase_line_ids:
                purchase.append(rec.order_id.id)
            contract.purchase_ids = [(6, 0, purchase)]

    @api.constrains('create_in_state_contract')
    def _constrains_create_in_state_contract(self):
        for pay in self:
            if pay.create_in_state_contract == 'confirm' and not self.env.user.has_group(
                    'purchase_contract_management.group_create_advance_payment_contract_confirmed'):
                raise ValidationError(_('You have not access to create confirmed payment.'))

    def create_contract_adv_payment(self):
        if self.amount <= 0.0:
            raise ValidationError(_("The payment amount cannot be negative or zero."))
        if self.create_in_state_contract == 'confirm':
            self.post()
        if self.env.context.get('active_id'):
            contract_id = self.env['purchase.contract'].browse(self.env.context.get('active_id'))
            contract_id.write({'account_payment_ids': [(4, self.id)]})
        return True

    def cancel(self):
        res = super(AccountPayment, self).cancel()
        for rec in self:
            rec.contract_id.total_advance_payment -= rec.amount
        return res

    def post(self):
        res = super(AccountPayment, self).post()
        for rec in self:
            rec.contract_id.total_advance_payment += rec.amount
        return res

    def action_draft(self):
        res = super(AccountPayment, self).action_draft()
        for rec in self:
            rec.contract_id.total_advance_payment -= rec.amount
        return res

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        res = super(AccountPayment, self)._onchange_partner_id()
        self.contract_id = False
        return res

    @api.onchange('contract_id')
    def _onchange_contract_id(self):
        self.purchase_id = False
