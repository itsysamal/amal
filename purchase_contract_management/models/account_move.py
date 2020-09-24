from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    contract_id = fields.Many2one('purchase.contract', string="Purchase Contract", readonly=True)

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    contract_id = fields.Many2one('purchase.contract',related='move_id.contract_id', string="Purchase Contract", readonly=True,store=True)
