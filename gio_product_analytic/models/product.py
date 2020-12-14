# -*- coding: utf-8 -*-
# Copyright: giordano.ch AG

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = "product.template"

    gio_analytic_account = fields.Many2one('account.analytic.account', string="ANALYTIC ACCOUNT")
    gio_analytic_tag = fields.Many2one('account.analytic.tag', string="ANALYTIC TAG", copy=False)

    # added by doaa
    @api.model
    def create(self, vals):
        res = super(ProductTemplate, self).create(vals)
        name = res.name
        default_code = res.default_code
        analytic_name = str(default_code) + '/' + name
        print("create")
        res.gio_analytic_account = self.env['account.analytic.account'].create(
            {'name': analytic_name, 'product_id': res.id}).id
        return res

    # added by doaa
    def write(self, vals):
        if 'name' in vals and 'default_code' not in vals:
            name = vals['name']
            default_code = self.default_code
            analytic_name = default_code + '/' + name
            if not self.gio_analytic_account.product_id:
                self.gio_analytic_account.product_id = self.id
            if self.gio_analytic_account:
                self.gio_analytic_account.name = analytic_name
                # else:
                #     print("write")
                #     self.gio_analytic_account = self.env['account.analytic.account'].create(
                #         {'name': analytic_name, 'product_id': self.id}).id

        if 'name' not in vals and 'default_code' in vals:
            name = self.name
            default_code = vals['default_code']
            analytic_name = default_code + '/' + name
            if not self.gio_analytic_account.product_id:
                self.gio_analytic_account.product_id = self.id
            if self.gio_analytic_account:
                self.gio_analytic_account.name = analytic_name
                # else:
                #     self.gio_analytic_account = self.env['account.analytic.account'].create(
                #         {'name': analytic_name, 'product_id': self.id}).id
        if 'name' in vals and 'default_code' in vals:
            name = vals['name']
            default_code = vals['default_code']
            analytic_name = default_code + '/' + name
            if not self.gio_analytic_account.product_id:
                self.gio_analytic_account.product_id = self.id
            if self.gio_analytic_account:
                self.gio_analytic_account.name = analytic_name
                # else:
                #     self.gio_analytic_account = self.env['account.analytic.account'].create(
                #         {'name': analytic_name, 'product_id': self.id}).id
        return super(ProductTemplate, self).write(vals)

        # def compute_analytic_account(self):
        # name_variants = rec.product_variant_id.name
        # default_code_variants = rec.product_variant_id.default_code
        # analytic_name_variants = str(default_code_variants) + '/' + name_variants
        # analytic_obj_varints = self.env['account.analytic.account'].search(
        #     [('product_product_id', '=', rec.product_variant_id.id)])
        # if analytic_obj_varints:
        #     for analytic in analytic_obj_varints:
        #         analytic.name = analytic_name_variants
        #         rec.product_variant_id.gio_analytic_account = analytic.id
        # else:
        #     rec.gio_analytic_account = self.env['account.analytic.account'].create(
        #         {'name': analytic_name, 'product_product_id': rec.product_variant_id.id}).id


# added by doaa
class AccountAnalyticAccount(models.Model):
    _inherit = "account.analytic.account"

    product_id = fields.Many2one('product.template', string="Product Template")


class ProductProduct(models.Model):
    _inherit = "product.product"

    # added by doaa
    @api.model
    def create(self, vals):
        res = super(ProductProduct, self).create(vals)
        res.product_tmpl_id.default_code = res.default_code
        return res
