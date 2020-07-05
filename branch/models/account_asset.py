from odoo import api, fields, models, _


class AccountAsset(models.Model):
    _inherit = 'account.asset'

    def _default_branch_id(self):
        branch_id = self.env['res.users'].browse(self._uid).branch_id.id or False
        return branch_id

    branch_id = fields.Many2one('res.branch', default=_default_branch_id)

    def validate(self):
        res = super(AccountAsset, self).validate()
        for asset in self:
            asset.depreciation_move_ids.write({'branch_id': asset.branch_id.id})
        return res

class AccountAccount(models.Model):
    _inherit = 'account.account'

    def _default_branch_id(self):
        branch_id = self.env['res.users'].browse(self._uid).branch_id.id or False
        return branch_id

    branch_id = fields.Many2one('res.branch', default=_default_branch_id)

