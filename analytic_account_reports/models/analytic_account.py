# -*- coding: utf-8 -*-
# Copyright: giordano.ch AG

from odoo import models, fields, api


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    qty_purchased = fields.Float(compute='_compute_qty_purchased_sold_balance', string='QTY PURCHASED', digits=(12, 2))
    unit_price_purchased = fields.Float(compute='_compute_qty_purchased_sold_balance', string='سعر الشراء $',
                                        digits=(12, 2))
    cost_purchased = fields.Float(compute='_compute_qty_purchased_sold_balance', string='Purchase Cost', digits=(12, 2))
    qty_sold = fields.Float(compute='_compute_qty_purchased_sold_balance', string='QTY SOLD', digits=(12, 2))
    balance_so_po = fields.Float(compute='_compute_qty_purchased_sold_balance', string='BALANCE', digits=(12, 2))
    vendor_id = fields.Many2one('res.partner', compute='get_product_vendor_id', string='Supplier')
    pro_category_id = fields.Many2one("product.category", related='product_id.categ_id', string="Product Category")
    attribute_line_ids = fields.Many2many('product.template.attribute.line', compute='get_product_attribute_line_ids',
                                          string="Attributes")
    product_template_attribute_value_ids = fields.Many2many('product.template.attribute.value',
                                                            compute='get_product_template_attribute_value_ids',
                                                            string="Attributes",
                                                            readonly=True)
    cost_revenue = fields.Float(compute='_compute_cost_revenue', string='Cost Of Revenue', digits=(12, 2))
    total_cost_revenue = fields.Float(compute='_compute_cost_revenue', string='Total Cost Of Revenue', digits=(12, 2))
    total_cost_per_qty = fields.Float(compute='_compute_cost_revenue', digits=(12, 2),
                                      string='تكلفة الطن total cost/qty')
    total_revenue_income_other = fields.Float(compute='_compute_cost_revenue', string='Revenue', digits=(12, 2))
    total_profit = fields.Float(compute='_compute_cost_revenue', string='Profit', digits=(12, 2))
    total_qty_result = fields.Float(compute='_compute_cost_revenue', digits=(12, 2), string='ناتج الكمية المباعة')
    total_balance = fields.Float(compute='_compute_cost_revenue', digits=(12, 2), string='سعر التعادل')
    account_expense_collection_ids = fields.One2many('account.expense.collection', 'analytic_account_id')
    po_multi_cur_ids = fields.One2many('purchase.multi.currency', 'analytic_account_id', string="سعر الشراء")

    def get_product_vendor_id(self):
        for rec in self:
            if rec.product_id:
                if rec.product_id.seller_ids:
                    for ven in rec.product_id.seller_ids:
                        rec.vendor_id = ven.name
                        break
                else:
                    rec.vendor_id = False
            else:
                rec.vendor_id = False

    @api.depends('product_id')
    def get_product_template_attribute_value_ids(self):
        for rec in self:
            all_att = []
            if rec.product_id:
                if rec.product_id.product_variant_ids:
                    for var in rec.product_id.product_variant_ids:
                        for line in var.product_template_attribute_value_ids:
                            if line.attribute_line_id.print_in_analytic_reports is True:
                                all_att.append(line.id)
            rec.product_template_attribute_value_ids = [(6, 0, all_att)]

    def _compute_qty_purchased_sold_balance(self):
        po_line_obj = self.env['purchase.order.line']
        so_line_obj = self.env['sale.order.line']
        for account in self:
            qty_purchased = 0.0
            qty_sold = 0.0
            price_unit = 0.0
            cost_purchased = 0.0
            all_currency = []
            all_po_cur_amount = []
            qty_purchase_obj = po_line_obj.search(
                [('account_analytic_id', '=', account.id), ('state', 'in', ('purchase', 'done'))])

            for line in qty_purchase_obj:
                all_currency.append(line.currency_id)
                qty_purchased += line.product_qty
                if line.currency_id != self.env.user.company_id.currency_id:
                    cost_purchased += line.price_unit / line.currency_id.rate
                else:
                    cost_purchased += line.price_unit

            for cur in set(all_currency):
                all_po_currency = []
                price_unit = 0.0
                for line in qty_purchase_obj:
                    if cur.id == line.currency_id.id:
                        price_unit += line.price_unit
                if account.po_multi_cur_ids:
                    for rec in account.po_multi_cur_ids:
                        all_po_currency.append(rec.currency_id)
                        if rec.currency_id == cur:
                            rec.amount = price_unit
                        all_po_cur_amount.append(rec.id)
                    if cur not in all_po_currency:
                        all_po_currency.append(cur)
                        vals = {
                            "name": str(price_unit) + '  ' + str(cur.name),
                            "currency_id": cur.id,
                            "analytic_account_id": account.id,
                            "amount": price_unit,
                        }

                        po_multi_cur_obj = self.env["purchase.multi.currency"].create(vals)
                        all_po_cur_amount.append(po_multi_cur_obj.id)
                else:
                    all_po_currency.append(cur)
                    vals = {
                        "name": str(price_unit) + '  ' + str(cur.name),
                        "currency_id": cur.id,
                        "analytic_account_id": account.id,
                        "amount": price_unit,
                    }

                    po_multi_cur_obj = self.env["purchase.multi.currency"].create(vals)
                    all_po_cur_amount.append(po_multi_cur_obj.id)
            account.po_multi_cur_ids = [(6, 0, all_po_cur_amount)]

            qty_sold_obj = so_line_obj.search(
                [('sale_analytic_account_id', '=', account.id), ('state', 'in', ('sale', 'done'))])
            for line in qty_sold_obj:
                qty_sold += line.product_uom_qty

            account.qty_purchased = qty_purchased
            account.unit_price_purchased = price_unit
            account.cost_purchased = cost_purchased
            account.qty_sold = qty_sold
            account.balance_so_po = account.qty_purchased - account.qty_sold

    def _compute_cost_revenue(self):
        analytics_line_obj = self.env['account.analytic.line']
        for account in self:
            all_exp = []
            all_accounts = []
            cost_revenue = 0.0
            cost_expense = 0.0
            total_revenue_income_other = 0.0
            cost_analytics_line_obj = analytics_line_obj.search(
                [('account_id', '=', account.id)])
            all_exp_accounts = []
            for line in cost_analytics_line_obj:
                if line.general_account_id.is_cost_revenue is True:
                    cost_revenue += line.amount
                if line.general_account_id.is_expense:
                    all_exp_accounts.append(line.general_account_id)
                if line.general_account_id.user_type_id.id in (13, 14):
                    total_revenue_income_other += line.amount
            account.account_expense_collection_ids = [(6, 0, [])]
            total_cost_expense = 0.0
            for acc in set(all_exp_accounts):
                cost_expense = 0.0
                exp_analytics_line_obj = analytics_line_obj.search(
                    [('account_id', '=', account.id), ('general_account_id', '=', acc.id)])
                for analytics_line in exp_analytics_line_obj:
                    cost_expense += analytics_line.amount
                if account.account_expense_collection_ids:
                    for rec in account.account_expense_collection_ids:
                        all_accounts.append(rec.account_id.id)
                        if acc == rec.account_id:
                            rec.name = str(rec.account_id.name) + ' : ' + str(cost_expense)
                            rec.amount = cost_expense
                        # all_exp.append(rec.id)
                    if acc not in all_accounts:
                        all_accounts.append(acc.id)
                        vals = {
                            "name": str(acc.name) + ' : ' + str(cost_expense),
                            "account_id": acc.id,
                            "analytic_account_id": account.id,
                            "amount": cost_expense,
                        }

                        exp_obj = self.env["account.expense.collection"].create(vals)
                        all_exp.append(exp_obj.id)
                        account.account_expense_collection_ids = [(6, 0, all_exp)]

                else:
                    all_accounts.append(acc.id)
                    vals = {
                        "name": str(acc.name) + ' : ' + str(cost_expense),
                        "account_id": acc.id,
                        "analytic_account_id": account.id,
                        "amount": cost_expense,
                    }

                    exp_obj = self.env["account.expense.collection"].create(vals)
                    all_exp.append(exp_obj.id)
                    account.account_expense_collection_ids = [(6, 0, all_exp)]
                total_cost_expense += cost_expense

            # account.account_expense_collection_ids = [(6, 0, all_exp)]
            account.cost_revenue = cost_revenue
            account.total_revenue_income_other = total_revenue_income_other
            # for exp in account.account_expense_collection_ids:
            #     cost_expense += exp.amount
            account.total_cost_revenue = account.cost_revenue + total_cost_expense
            if account.qty_purchased != 0.00:
                account.total_cost_per_qty = account.total_cost_revenue / account.qty_purchased
            else:
                account.total_cost_per_qty = 0.00
            account.total_profit = account.total_revenue_income_other - account.total_cost_revenue
            account.total_qty_result = account.total_revenue_income_other - (
                    account.total_cost_per_qty * account.qty_sold)
            if account.balance_so_po != 0.00:
                account.total_balance = (
                                                account.total_cost_revenue - account.total_revenue_income_other) / account.balance_so_po

            else:
                account.total_balance = 0.00

    def analytic_print_xls(self):
        self.ensure_one()
        active_record = self.env.context.get('active_ids', [])
        record = self.env['account.analytic.account'].browse(active_record)

        data = {
            'ids': self.ids,
            'model': self._name,
            'record': record.id,
        }
        return self.env.ref('analytic_account_reports.analytic_form_xls_id').report_action(self, data=data)


class ProductTemplateAttributeLine(models.Model):
    _inherit = 'product.template.attribute.line'

    print_in_analytic_reports = fields.Boolean("Print in Analytic Reports?")


class AccountAccount(models.Model):
    _inherit = 'account.account'

    is_cost_revenue = fields.Boolean("Print As Cost Of Revenue?")
    is_expense = fields.Boolean("Print As Expense?")


class AccountExpenseCollection(models.Model):
    _name = 'account.expense.collection'

    name = fields.Char("Name")
    amount = fields.Float("Amount", digits=(12, 2))
    account_id = fields.Many2one('account.account', string='Account')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytics Account')


class PurchaseMultiCurrency(models.Model):
    _name = 'purchase.multi.currency'

    name = fields.Char("Name")
    amount = fields.Float("Amount", digits=(12, 2))
    currency_id = fields.Many2one('res.currency', string='Currency')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytics Account')
