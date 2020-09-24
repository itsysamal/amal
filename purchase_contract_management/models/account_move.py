from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    contract_id = fields.Many2one('purchase.contract', string="Purchase Contract", readonly=True)
