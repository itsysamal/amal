# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _

class ContractOperationLine(models.Model):
    _name = 'contract.operation.line'
    _description = 'Contract Operation Lines'
    _rec_name = 'name'
    _order = 'name DESC'

    name = fields.Char(string="Name", required=True,copy=False)
    contract_id = fields.Many2one('purchase.contract',string="Purchase Contract")
    purchase_contract_line_id = fields.Many2one('purchase.contract.line',string="Purchase Contract Line")
    loading_area = fields.Char("Loading Area.")
    inspection_name = fields.Char("Inspection Name.")
    free_time = fields.Float("Free Time")
    trans_time = fields.Float("Trans Time")
    clearance_agent_id = fields.Many2one('res.partner', string="Clearance Agent Name",domain= "[('is_agent','=',True)]")
    sending_bank_details_date = fields.Date("Sending Bank Details Date")
    courier_name = fields.Char(string="Courier Name")
    in_bank_office_date = fields.Date("In Bank Office Date")
    out_bank_office_date = fields.Date("Out Bank Office Date")
    sent_to_clearance_date = fields.Date("Sent To Clearance Date")
    free_time_expiration_date = fields.Date("Free Time Expiration Date")
