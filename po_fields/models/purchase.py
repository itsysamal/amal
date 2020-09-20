# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class ResPartner(models.Model):
    _inherit = 'res.partner'
    is_broker = fields.Boolean(string="Broker",  )
    is_agent = fields.Boolean(string="Agent", )
class origin(models.Model):
    _name = 'origin'
    _rec_name = 'name'
    _description = ''

    name= fields.Char(string="origin", required=True, )



class purchaseOrder(models.Model):
    _inherit = 'purchase.order.line'
    e_t_s_date = fields.Date(string="E.T.S ", required=False, default=fields.Date.context_today)
    e_t_a_date = fields.Date(string="E.T.A ", required=False, default=fields.Date.context_today)
    Arrival_After_date = fields.Date(string="Arrival After", required=False, default=fields.Date.context_today)
    broker_id = fields.Many2one(comodel_name="res.partner", string="Broker Name", required=False, domain= "[('is_broker','=',True)]",)
    agent_id = fields.Many2one(comodel_name="res.partner", string="Agent", required=False, domain= "[('is_agent','=',True)]",)
    commission = fields.Float(string="Commission",  required=False, )
    full_container_load = fields.Char(string="Full Container Load", required=False, )
    packing = fields.Char(string="Packing", required=False, )
    bank_name = fields.Char(string="BANK NAME", required=False, )
    power_of_attorney = fields.Char(string="Power of attorney ", required=False, )
    shipping_line = fields.Char(string="Shipping line ", required=False, )
    bill_of_lading_number = fields.Char(string="Bill of Lading number ", required=False, )
    free_time= fields.Float(string="FREE TIME ",  required=False, )
    trans_time = fields.Float(string="Trans time ", required=False, )
    date_of_sending_bank  = fields.Date(string="Date of sending bank", required=False, default=fields.Date.context_today)
    courier= fields.Char(string="Courier", required=False, )
    tracking_no= fields.Char(string="Tracking No.", required=False, )
    in_bank_date = fields.Date(string="In Bank /office", required=False, default=fields.Date.context_today)
    out_bank_date = fields.Date(string="Out bank /office", required=False, default=fields.Date.context_today)
    sent_for_clearance= fields.Date(string="Sent for clearance", required=False, default=fields.Date.context_today)
    gomrk_cert= fields.Char(string="الشهادة الجمركية", required=False, )
    end_of_date= fields.Date(string="تاريخ انتهاء", required=False, default=fields.Date.context_today)
    permission_of_date= fields.Date(string="فترة السماح", required=False, default=fields.Date.context_today)
    time_of_day= fields.Float(string="الوقت المتبقى باليوم",  required=False, )
    storage_letter = fields.Char(string="خطاب السعة التخزينية", required=False, )
    debit_note_storage= fields.Char(string="DEBIT NOTE STORAGE", required=False, )
    demurrage_qualtiy = fields.Char(string="DEMURRAGE QUALITY	", required=False, )
    extra_charges= fields.Float(string="EXTRA CHARGES",  required=False, )
    note= fields.Char(string="NOTE", required=False, )
    origin_id = fields.Many2one(comodel_name="origin", string="Origin", required=False, )

