from odoo import api, fields, models, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    conversion_id = fields.Many2one('product.conversion', related='group_id.conversion_id', string="Product Conversion",
                                    store=True, readonly=True)


class StockMove(models.Model):
    _inherit = 'stock.move'

    conversion_id = fields.Many2one('product.conversion', string="Product Conversion",
                                    related='picking_id.conversion_id',
                                    readonly=True, store=True)
    product_remove_id = fields.Many2one('product.remove', string="Product To Remove", readonly=True)
    product_add_id = fields.Many2one('product.add', string="Product To Add", readonly=1)


class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    conversion_id = fields.Many2one('product.conversion', string="Product Conversion", readonly=True)
    product_remove_id = fields.Many2one('product.remove', string="Product To Remove", readonly=True)
