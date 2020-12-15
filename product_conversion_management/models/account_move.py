from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    conversion_id = fields.Many2one('product.conversion', string="Product Conversion", readonly=True)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    conversion_id = fields.Many2one('product.conversion',related='move_id.conversion_id', string="Product Conversion", readonly=True,store=True,)
