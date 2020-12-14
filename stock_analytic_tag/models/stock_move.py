##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    analytic_tag_ids = fields.Many2many(
        'account.analytic.tag',
        states={'done': [('readonly', True)]},
    )

    def _prepare_account_move_line(
        self, qty, cost, credit_account_id, debit_account_id, description):
        self.ensure_one()
        res = super(StockMove, self)._prepare_account_move_line(
            qty, cost, credit_account_id, debit_account_id, description
        )
        if not self.analytic_tag_ids or not res:
            return res
        for num in range(0, 2):
                # res[num][1].update({"analytic_tag_ids": [(6, 0, self.analytic_tag_ids.ids)]})
                res[num][2].update({"analytic_tag_ids": [(6, 0, self.analytic_tag_ids.ids)]})
        return res

