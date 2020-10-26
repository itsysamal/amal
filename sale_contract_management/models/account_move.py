from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    sale_contract_id = fields.Many2one('sale.contract', string="Sale Contract", readonly=True)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    sale_contract_id = fields.Many2one('sale.contract', related='move_id.sale_contract_id', string="Sale Contract",
                                       readonly=True, store=True, )
