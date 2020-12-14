from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo import models, fields, api, exceptions, _


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    sale_contract_id = fields.Many2one('sale.contract', string="Sale Contract", readonly=True, store=True,
                                       states={'draft': [('readonly', False)]})
    sale_create_in_state_contract = fields.Selection([('draft', 'Draft'),
                                                      ('confirm', 'Confirm')],
                                                     default='draft',
                                                     string="Payment Status")
    sale_check_contract_payment = fields.Boolean()

    sale_id = fields.Many2one('sale.order', "Sale",
                              readonly=True, states={'draft': [('readonly', False)]})
    sale_ids = fields.Many2many('sale.order', string='Sale', compute='compute_sale_ids')

    @api.depends('sale_contract_id.sale_line_ids')
    def compute_sale_ids(self):
        for contract in self:
            sale = []
            for rec in contract.sale_contract_id.sale_line_ids:
                sale.append(rec.order_id.id)
            contract.sale_ids = [(6, 0, sale)]

    @api.constrains('sale_create_in_state_contract')
    def _constrains_sale_create_in_state_contract(self):
        for pay in self:
            if pay.sale_create_in_state_contract == 'confirm' and not self.env.user.has_group(
                    'sale_contract_management.group_create_advance_payment_sale_contract_confirmed'):
                raise ValidationError(_('You have not access to create confirmed payment.'))

    def sale_create_contract_adv_payment(self):
        if self.amount <= 0.0:
            raise ValidationError(_("The payment amount cannot be negative or zero."))
        if self.sale_create_in_state_contract == 'confirm':
            self.post()
        if self.env.context.get('active_id'):
            sale_contract_id = self.env['sale.contract'].browse(self.env.context.get('active_id'))
            sale_contract_id.write({'account_payment_ids': [(4, self.id)]})
        return True

    def create_sale_adv_payment(self):
        if self.amount <= 0.0:
            raise ValidationError(_("The payment amount cannot be negative or zero."))
        if self.create_in_state_sale == 'confirm':
            self.post()
        if self.env.context.get('active_id'):
            sale_id = self.env['sale.order'].browse(self.env.context.get('active_id'))
            sale_id.write({'adv_payment_ids': [(4, self.id)]})
            for sale in sale_id.adv_payment_ids:
                if sale_id.sale_contract_id:
                    sale.write({'sale_contract_id': sale_id.sale_contract_id.id})
        return True

    def cancel(self):
        res = super(AccountPayment, self).cancel()
        for rec in self:
            rec.sale_contract_id.total_advance_payment -= rec.amount
        return res

    def post(self):
        res = super(AccountPayment, self).post()
        for rec in self:
            rec.sale_contract_id.total_advance_payment += rec.amount
        return res

    def action_draft(self):
        res = super(AccountPayment, self).action_draft()
        for rec in self:
            rec.sale_contract_id.total_advance_payment -= rec.amount
        return res

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        res = super(AccountPayment, self)._onchange_partner_id()
        self.sale_contract_id = False
        return res

    @api.onchange('sale_contract_id')
    def _onchange_sale_contract_id(self):
        self.sale_id = False
