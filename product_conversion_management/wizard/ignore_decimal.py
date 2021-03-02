from odoo import api, fields, models


class IgnoreDecimal(models.TransientModel):
    _name = "ignore.decimal"
    _description = "Warning Message"

    message = fields.Text(string="Message")
    product_conversion_id = fields.Many2one('product.conversion', string='Product Conversion')

    # @api.model
    # def action_cancel(self):
    #     return {'type': 'ir.actions.act_window_close'}

    def ignore_decimal_numbers(self):
        for rec in self:
            rec.product_conversion_id.ignore_decimal_numbers = True
