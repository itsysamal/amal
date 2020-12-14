# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _


class SaleContractOperationLine(models.Model):
    _name = 'sale.contract.operation.line'
    _description = 'Sale Contract Operation Lines'
    _rec_name = 'name'
    _order = 'name DESC'

    name = fields.Char(string="Name", required=True, copy=False)
    sale_contract_id = fields.Many2one('sale.contract', string="Sale Contract")
    sale_contract_line_id = fields.Many2one('sale.contract.line', string="Sale Contract Line")
    loading_area = fields.Char("Loading Area.")
    inspection_name = fields.Char("Inspection Name.")
    free_time = fields.Datetime("Free Time")
    trans_time = fields.Datetime("Trans Time")
    clearance_agent_id = fields.Many2one('res.partner', string="Clearance Agent Name", domain="[('is_agent','=',True)]")
    sending_bank_details_date = fields.Date("Sending Bank Details Date")
    courier_name = fields.Char(string="Courier Name")
    in_bank_office_date = fields.Date("In Bank Office Date")
    out_bank_office_date = fields.Date("Out Bank Office Date")
    sent_to_clearance_date = fields.Date("Sent To Clearance Date")
    free_time_expiration_date = fields.Date("Free Time Expiration Date")

    sale_contract_line_ids = fields.Many2many('sale.contract.line', string='sale Contract Line',
                                              compute='compute_sale_contract_line_ids')

    @api.depends('sale_contract_id.sale_contract_line_ids')
    def compute_sale_contract_line_ids(self):
        for contract in self:
            ship_line = []
            for rec in contract.sale_contract_id.sale_contract_line_ids:
                if rec._origin.id:
                    ship_line.append(rec.id)
            contract.sale_contract_line_ids = [(6, 0, ship_line)]
