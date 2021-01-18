# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _


class SaleShipCostLine(models.Model):
    _name = 'sale.ship.cost.line'
    _description = 'Sale Ship Cost Line'
    _rec_name = 'name'
    _order = 'name DESC'

    name = fields.Char(string="Description", required=True, copy=False)
    sale_contract_id = fields.Many2one('sale.contract', string="Sale Contract")
    sale_contract_line_id = fields.Many2one('sale.contract.line', string="Sale Contract Line")
    freight = fields.Float("Freight")
    thc = fields.Float("THC")
    currency_id = fields.Many2one('res.currency', string="Currency",default=lambda self: self.env.company.currency_id)
    sale_contract_line_ids = fields.Many2many('sale.contract.line', string='Sale Contract Line',
                                                  compute='compute_sale_contract_line_ids')

    @api.depends('sale_contract_id.sale_contract_line_ids')
    def compute_sale_contract_line_ids(self):
        for contract in self:
            ship_line = []
            for rec in contract.sale_contract_id.sale_contract_line_ids:
                if rec._origin.id:
                    ship_line.append(rec.id)
            contract.sale_contract_line_ids = [(6, 0, ship_line)]
