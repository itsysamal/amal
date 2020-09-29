# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _


class ShipCostLine(models.Model):
    _name = 'ship.cost.line'
    _description = 'Purchase Contract Lines'
    _rec_name = 'name'
    _order = 'name DESC'

    name = fields.Char(string="Description", required=True, copy=False)
    contract_id = fields.Many2one('purchase.contract', string="Purchase Contract")
    purchase_contract_line_id = fields.Many2one('purchase.contract.line', string="Purchase Contract Line")
    freight = fields.Float("Freight")
    thc = fields.Float("THC")
    currency_id = fields.Many2one('res.currency', string="Currency")
    purchase_contract_line_ids = fields.Many2many('purchase.contract.line', string='Purchase Contract Line',
                                                  compute='compute_purchase_contract_line_ids')

    @api.depends('contract_id.purchase_contract_line_ids')
    def compute_purchase_contract_line_ids(self):
        for contract in self:
            ship_line = []
            for rec in contract.contract_id.purchase_contract_line_ids:
                if rec._origin.id:
                    ship_line.append(rec.id)
            contract.purchase_contract_line_ids = [(6, 0, ship_line)]
