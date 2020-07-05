# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    branch_id = fields.Many2one('res.branch')

    # def _sub_select(self):
    #     return super(AccountInvoiceReport, self)._sub_select() + ", ai.branch_id as branch_id"

    def _select(self):
        return super(AccountInvoiceReport, self)._select() + ", move.branch_id as branch_id"

    def _group_by(self):
        return super(AccountInvoiceReport, self)._group_by() + ", move.branch_id"