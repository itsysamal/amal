# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _


class ContractType(models.Model):
    _name = 'contract.type'
    _description = 'Contract Type'
    _rec_name = 'name'

    name = fields.Char(string="Contract Type", required=True, copy=False)


class ContractDeliverTo(models.Model):
    _name = 'contract.deliver.to'
    _description = 'Contract Deliver To'
    _rec_name = 'name'

    name = fields.Char(string="Contract Deliver To", required=True, copy=False)


class ContainerSize(models.Model):
    _name = 'container.size'
    _description = 'Container Size'
    _rec_name = 'name'

    name = fields.Char(string="Container Size", required=True, copy=False)
