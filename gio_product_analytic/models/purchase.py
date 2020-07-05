# -*- coding: utf-8 -*-
# Copyright: giordano.ch AG

from odoo import models, fields, api


class Purchase(models.Model):
    _inherit = 'purchase.order.line'


    @api.onchange('product_id')
    def onchange_product_id_changes(self):
        if self.product_id:
            self.analytic_tag_ids = self.product_id.gio_analytic_tag
            self.account_analytic_id = self.product_id.gio_analytic_account