from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo import models, fields, api, exceptions, _


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    contract_id = fields.Many2one('purchase.contract', string="Purchase Contract", readonly=True)
    create_in_state_contract = fields.Selection([('draft', 'Draft'),
                                                 ('confirm', 'Confirm')],
                                                default='confirm',
                                                string="Payment Status")

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
