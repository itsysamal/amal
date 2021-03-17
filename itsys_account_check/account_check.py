from odoo import api, fields, models, _
from odoo.exceptions import UserError


class account_check(models.Model):
    _name = 'account.check'

    def open_payment_matching_screen(self):
        # Open reconciliation view for customers/suppliers
        move_line_id = False
        # for move_line in self.move_line_ids:
        #     if move_line.account_id.reconcile:
        #         move_line_id = move_line.id
        #         break
        # move_line_id=129
        if not self.partner_id:
            raise UserError(_("Payments without a customer can't be matched"))
        action_context = {'company_ids': [self.company_id.id], 'partner_ids': [self.partner_id.commercial_partner_id.id]}
        # if self.partner_type == 'customer':
        action_context.update({'mode': 'customers'})
        # elif self.partner_type == 'supplier':
        #     action_context.update({'mode': 'suppliers'})
        # action_context.update({'mode': 'customers'})
        # action_context.update({'mode': 'suppliers,customers'})

        if move_line_id:
            action_context.update({'move_line_id': move_line_id})

        print('action_context',action_context)
        return {
            'type': 'ir.actions.client',
            'tag': 'manual_reconciliation_view',
            'context': action_context,
        }
    @api.model
    def _default_state(self):
        if self._context.get('default_collect_ok'):
            # self.collect_ok=True
            return 'draft_collect'
        else:
            # self.pay_ok=True
            return 'draft_pay'

    @api.depends('currency_id', 'company_id.currency_id')
    def _compute_not_company_currency(self):
        self.not_company_currency = self.currency_id and self.currency_id != self.company_id.currency_id

    partner_to_id = fields.Many2one('res.partner', string='Customer to')

    name = fields.Char('Name', readonly=True)
    pay_ok = fields.Boolean('pay_ok')
    collect_ok = fields.Boolean('collect_ok')
    to_check = fields.Boolean('To Review')
    date = fields.Date('Date', required=True)
    due_date = fields.Date('Due Date')
    amount = fields.Float('Amount')
    ref = fields.Char('Check Number', required=False)
    comm = fields.Char('Bank')
    journal_id = fields.Many2one('account.journal', string='Journal', required=True, domain=[('type', '=', 'bank')])
    partner_id = fields.Many2one('res.partner', string='Partner', required=True)
    state = fields.Selection([('draft_collect', 'New'),
                              ('draft_pay', 'New'),
                              ('open', 'Open'),
                              ('receive', 'Paper Receive'),
                              ('deposit', 'Bank Deposit'),
                              ('collect', 'Collect Cheque'),
                              ('return', 'Return Check'),
                              ('cash_payment', 'Cash Payment'),
                              ('return_client', 'Return to Client'),
                              ('cheque_hashed', 'Hash cheque to supplier'),
                              ('return_cheque_hashed', 'Return hashed cheque to supplier'),
                              ('deposit_direct', 'Direct Deposit'),
                              ('generate_supp', 'Generate Cheque - Supplier'),
                              ('bank_payment', 'Bank Payment'),
                              ('cheque_return', 'Cheque Return from bank'),
                              ('confirm', 'Closed'),
                              ('cancel', 'Cancel'), ],
                             'Status', required=True, default=_default_state, readonly="1",
                             copy=False, )

    supplier_id = fields.Many2one(comodel_name='res.partner', domain=[('supplier', '=', True)],
                                  string='Hashed to Supplier')
    company_id = fields.Many2one(comodel_name='res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one(comodel_name='res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id, )

    not_company_currency = fields.Boolean('Use Custom Currency Rate', compute='_compute_not_company_currency')

    currency_rate = fields.Float(string='System Currency Rate', compute='_compute_currency_rate',
                                 digits=(16, 13), readonly=True, store=True, help="Currency rate of this invoice")
    use_custom_rate = fields.Boolean('Use Custom Rate', readonly=True, default=True,
                                     states={'draft': [('readonly', False)]})
    custom_rate = fields.Float(string='Custom Rate', digits=(16, 13), readonly=True)
    company_currency_id = fields.Many2one(comodel_name='res.currency', related='company_id.currency_id',
                                          string="Currency")
    line_ids=fields.One2many('check.lines','check_id')

    account_note_paper_id = fields.Many2one('account.account', string='Note Paper')
    account_under_collection_id = fields.Many2one('account.account', string='Check under collection')
    account_bank_collect_id = fields.Many2one('account.account', string='Bank Collect')
    generate_check_to_supplier = fields.Many2one('account.account', string='Generate check to supplier')
    bank_payment = fields.Many2one('account.account', string='Bank Payment')
    move_line_ids = fields.One2many('account.move.line', 'check_id', readonly=True, copy=False, ondelete='restrict')

    _sql_constraints = [
        ('amount_greater_than_zero', 'CHECK(amount > 0)', 'Error ! Amount cannot be zero or less')
    ]


    def compute_check_journal(self):
        for line in self:
            line.doc_count = self.env['account.move'].search_count([('name', '=', line.name),('ref', '=', line.ref)])

    doc_count = fields.Integer(compute='compute_check_journal')
    def document_view(self):
        self.ensure_one()
        domain = [
            ('name', '=', self.name), ('ref', '=', self.ref)
            ]
        return {
            'name': _('Journal Entries'),
            'domain': domain,
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',

        }


    def cancel(self):
        for lin in self:
            lin.write({'state': 'cancel'})
            journal_enteries = self.env['account.move'].search([
                ('ref', '=', lin.ref),
                ('name', '=', lin.name)])
            if journal_enteries:
                for rec in journal_enteries:
                    rec.button_cancel()
                    rec.state='cancel'



    @api.constrains('custom_rate')
    def _custom_rate_constrain(self):
        for rec in self:
            if rec.use_custom_rate:
                if rec.custom_rate <= 0:
                    raise Warning(_('Rate should be more than Zero'))

    @api.onchange('currency_id')
    def onchange_custom_rate(self):
        if self.currency_id:
            self.custom_rate = self.currency_id.rate

    @api.onchange('journal_id')
    def onchange_journal_id(self):
        if self.journal_id and self.journal_id.currency_id and self.journal_id.currency_id.id != self.currency_id.id:
            raise UserError(_('the currency must be like the currency in journal'))

    @api.depends('currency_id', 'not_company_currency')
    def _compute_currency_rate(self):
        rate = self.currency_id.rate
        self.currency_rate = rate or (self.currency_id and self.currency_id.rate) or 1

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('account.check') or '/'
        return super(account_check, self).create(vals)

    # @api.multi
    def unlink(self):
        if self.state != 'cancel':
            raise UserError(_('You can not delete a check that is not in cancel state'))
        return super(account_check, self).unlink()

    # def check_date(self):
    #     self.env.cr.execute("select max(date) from account_move where name='"+str(self.name)+"'")
    #     res = self.env.cr.fetchone()[0]
    #     if res and self.date < res:
    #         raise UserError(_('Date cannot be earlier than last move date'))

    def check_move_create(self, debit, credit):
        amount1=credit
        account_move_obj = self.env['account.move']
        if self.journal_id.currency_id.id != self.env.user.company_id.currency_id.id:
            jr_rate=self.journal_id.currency_id.rate or 1
            print("wwwwwwwwwwwwwww",jr_rate)
            debit = debit * jr_rate if jr_rate >= 1 else debit / jr_rate
            credit = credit *  jr_rate if  jr_rate >= 1 else credit / jr_rate
            print('ooooooooooooooooooooooooooooo',debit,credit)

        if self.not_company_currency:
            print("uuuuuuuuuuuuuuuuuuuuuu")
            currency = self.currency_id.id
            if not self._context.get('return_item'):
                amount_currency = amount1 #credit / self.custom_rate if self.custom_rate > 1 else credit * self.custom_rate
                negative_amount_currency = amount1 * -1 # (credit / self.custom_rate if self.custom_rate > 1 else credit * self.custom_rate) * -1
            else:
                negative_amount_currency = amount1 * -1 #(debit / self.custom_rate if self.custom_rate > 1 else debit * self.custom_rate) * -1
                amount_currency = amount1 #(debit / self.custom_rate if self.custom_rate > 1 else debit * self.custom_rate)
        else:
            currency = False
            negative_amount_currency = 0
            amount_currency = 0

        if self.journal_id.journal_state == 'receive':
            created_obj= account_move_obj.create({'name': self.name, 'ref': self.ref,
                                     'journal_id': self.journal_id.id,
                                     'line_ids': [(0, 0, {
                                         'name': self.name,
                                         'account_id': self.partner_id.property_account_receivable_id.id,
                                         'partner_id': self.partner_id.id,
                                         'currency_id': currency,
                                         'amount_currency': negative_amount_currency,
                                         'credit': credit,
                                         'debit': debit,
                                         'date_maturity': self.due_date,
                                     }), (0, 0, {
                                         'name': self.name,
                                         'account_id': self.journal_id.default_debit_account_id.id,
                                         'partner_id': self.partner_id.id,
                                         'currency_id': currency,
                                         'amount_currency': amount_currency,
                                         'credit': debit,
                                         'debit': credit,
                                         'date_maturity': self.due_date,
                                     })], 'date': self.date})

            created_obj.action_post()
            return True

        if self.journal_id.journal_state =='return_client':
            created_obj=account_move_obj.create({'name': self.name, 'ref': self.ref,
                                     'journal_id': self.journal_id.id,
                                     'line_ids': [(0, 0, {
                                         'name': self.name, 'account_id': self.journal_id.default_debit_account_id.id,
                                         'partner_id': self.partner_id.id,
                                         'currency_id': currency,
                                         'amount_currency': negative_amount_currency,
                                         'credit': credit, 'debit': debit, 'date_maturity': self.due_date,
                                     }), (0, 0, {
                                         'name': self.name, 'account_id': self.partner_id.property_account_receivable_id.id,
                                         'partner_id': self.partner_id.id,
                                         'currency_id': currency,
                                         'amount_currency': amount_currency,
                                         'credit': debit, 'debit': credit, 'date_maturity': self.due_date,
                                     })],'date': self.date
                                     ,'company_id': company_id})
            created_obj.action_post()
            return True

        if self.journal_id.journal_state == 'generate_supp':
            created_obj= account_move_obj.create({'name': self.name, 'ref': self.ref,
                                     'journal_id': self.journal_id.id,
                                     'line_ids': [(0, 0, {
                                         'name': self.name,
                                         'account_id': self.journal_id.default_debit_account_id.id,
                                         'partner_id': self.partner_id.id,
                                         'credit': credit,
                                         'debit': debit,
                                         'currency_id': currency,
                                         'amount_currency': negative_amount_currency,
                                         'date_maturity': self.due_date,
                                     }), (0, 0, {
                                         'name': self.name,
                                         'account_id': self.partner_id.property_account_payable_id.id,
                                         'partner_id':
                                             self.partner_id.id,
                                         'credit': debit,
                                         'debit': credit,
                                         'currency_id': currency,
                                         'amount_currency': amount_currency,
                                         'date_maturity': self.due_date,
                                     })], 'date': self.date})

            created_obj.action_post()
            return True


        if self.journal_id.journal_state=='cheque_return':
            created_obj=account_move_obj.create({'name': self.name, 'ref': self.ref,
                                     'journal_id': self.journal_id.id,
                                     'line_ids': [(0, 0, {
                                         'name': self.name, 'account_id': self.partner_id.property_account_payable_id.id,
                                         'currency_id': currency,
                                         'amount_currency': negative_amount_currency,
                                         'partner_id': self.partner_id.id,
                                         'credit': credit, 'debit': debit, 'date_maturity': self.due_date,
                                     }), (0, 0, {
                                         'name': self.name, 'account_id': self.journal_id.default_debit_account_id.id,
                                         'partner_id': self.partner_id.id,
                                         'currency_id': currency,
                                         'amount_currency': amount_currency,
                                         'credit': debit, 'debit': credit, 'date_maturity': self.due_date,
                                     })],'date': self.date
                                        , 'company_id': company_id})
            created_obj.action_post()
            return True


        if self.journal_id.journal_state == 'cheque_hashed':
            created_obj=account_move_obj.create({'name': self.name, 'ref': self.ref,
                                     'journal_id': self.journal_id.id,
                                     'line_ids': [(0, 0, {
                                         'name': self.name,
                                         'account_id': self.partner_id.property_account_payable_id.id,
                                         'partner_id': self.partner_id.id,
                                         'credit': credit,
                                         'debit': debit,
                                         'currency_id': currency,
                                         'amount_currency': negative_amount_currency,
                                         'date_maturity': self.due_date,
                                     }), (0, 0, {
                                         'name': self.name,
                                         'account_id': self.partner_id.property_account_payable_id.id,
                                         'partner_id': self.partner_id.id,
                                         'credit': debit,
                                         'debit': credit,
                                         'currency_id': currency,
                                         'amount_currency': amount_currency,
                                         'date_maturity': self.due_date,
                                     })], 'date': self.date})

            created_obj.action_post()
            return True

        created_obj=account_move_obj.create({'name': self.name, 'ref': self.ref,
                                 'journal_id': self.journal_id.id,
                                 'line_ids': [(0, 0, {
                                     'name': self.name,
                                     'account_id': self.journal_id.default_credit_account_id.id,
                                     'partner_id': self.partner_id.id,
                                     'credit': credit,
                                     'debit': debit,
                                     'currency_id': currency,
                                     'amount_currency': negative_amount_currency,
                                     'date_maturity': self.due_date,
                                 }), (0, 0, {
                                     'name': self.name,
                                     'account_id': self.journal_id.default_debit_account_id.id,
                                     'partner_id': self.partner_id.id,
                                     'credit': debit,
                                     'debit': credit,
                                     'currency_id': currency,
                                     'amount_currency': amount_currency,
                                     'date_maturity': self.due_date,
                                 })],
                                 'date': self.date})

        created_obj.action_post()
    def check_move_create(self ):


        account_move_obj = self.env['account.move']


        if self.journal_id.journal_state == 'receive':
            total_debit=0
            total_credit=0
            total_amount_currency=0
            total_negative_amount_currency=0
            line_ids = []
            line_name=''
            for line in self.line_ids:
                if not line.account_note_paper_id:
                    raise UserError(_('You must enter account_note_paper_id account'))
                amount1 = line.amount
                credit=line.amount
                debit=0.0
                if self.journal_id.currency_id.id != self.env.user.company_id.currency_id.id:
                    jr_rate = self.journal_id.currency_id.rate or 1
                    print("wwwwwwwwwwwwwww", jr_rate)
                    debit = debit * jr_rate if jr_rate >= 1 else debit / jr_rate
                    credit = credit * jr_rate if jr_rate >= 1 else credit / jr_rate
                    print('ooooooooooooooooooooooooooooo', debit, credit)

                if self.not_company_currency:
                    print("uuuuuuuuuuuuuuuuuuuuuu")
                    currency = self.currency_id.id
                    if not self._context.get('return_item'):
                        amount_currency = amount1  # credit / self.custom_rate if self.custom_rate > 1 else credit * self.custom_rate
                        negative_amount_currency = amount1 * -1  # (credit / self.custom_rate if self.custom_rate > 1 else credit * self.custom_rate) * -1
                    else:
                        negative_amount_currency = amount1 * -1  # (debit / self.custom_rate if self.custom_rate > 1 else debit * self.custom_rate) * -1
                        amount_currency = amount1  # (debit / self.custom_rate if self.custom_rate > 1 else debit * self.custom_rate)
                else:
                    currency = False
                    negative_amount_currency = 0
                    amount_currency = 0
                total_credit+=credit
                total_debit+=debit
                total_amount_currency+=amount_currency
                total_negative_amount_currency+=negative_amount_currency
                line_name+='- '+line.ref
                line_ids.append((0, 0, {
                                             'name': line.ref,
                                             'account_id': line.account_note_paper_id.id,
                                             'partner_id': self.partner_id.id,
                    'partner_to_id': self.partner_to_id and self.partner_to_id.id or False,

                    'currency_id': currency,
                                             'amount_currency': amount_currency,
                                             'credit': debit,
                                             'debit': credit,
                                             'date_maturity': line.date,
                    'chemical_bank_id':line.chemical_bank_id.id,
                    'bank_id': line.bank_id.id,

                }))
            line_ids.append((0, 0, {
                    'name': line_name,
                    'account_id': self.partner_id.property_account_receivable_id.id,
                    'partner_id': self.partner_id.id,
                'partner_to_id':self.partner_to_id and self.partner_to_id.id or False,

                'currency_id': currency,
                    'amount_currency': total_negative_amount_currency,
                    'credit': total_credit,
                    'debit': total_debit,
                    'date_maturity': line.date,
                'chemical_bank_id': line.chemical_bank_id.id,
                'bank_id': line.bank_id.id,
                'check_id':self.id,
                }))
            created_obj= account_move_obj.create({'name': self.name, 'ref': self.ref,
                                         'journal_id': self.journal_id.id,
                                         'line_ids': line_ids, 'date': self.date})

            created_obj.action_post()
            return True

        if self.journal_id.journal_state == 'deposit':
            total_debit=0
            total_credit=0
            total_amount_currency=0
            total_negative_amount_currency=0
            line_ids = []

            for line in self.line_ids:
                if not line.account_under_collection_id:
                    raise UserError(_('You must enter account_note_paper_id account'))
                amount1 = line.amount
                credit=line.amount
                debit=0.0
                if self.journal_id.currency_id.id != self.env.user.company_id.currency_id.id:
                    jr_rate = self.journal_id.currency_id.rate or 1
                    print("wwwwwwwwwwwwwww", jr_rate)
                    debit = debit * jr_rate if jr_rate >= 1 else debit / jr_rate
                    credit = credit * jr_rate if jr_rate >= 1 else credit / jr_rate
                    print('ooooooooooooooooooooooooooooo', debit, credit)

                if self.not_company_currency:
                    print("uuuuuuuuuuuuuuuuuuuuuu")
                    currency = self.currency_id.id
                    if not self._context.get('return_item'):
                        amount_currency = amount1  # credit / self.custom_rate if self.custom_rate > 1 else credit * self.custom_rate
                        negative_amount_currency = amount1 * -1  # (credit / self.custom_rate if self.custom_rate > 1 else credit * self.custom_rate) * -1
                    else:
                        negative_amount_currency = amount1 * -1  # (debit / self.custom_rate if self.custom_rate > 1 else debit * self.custom_rate) * -1
                        amount_currency = amount1  # (debit / self.custom_rate if self.custom_rate > 1 else debit * self.custom_rate)
                else:
                    currency = False
                    negative_amount_currency = 0
                    amount_currency = 0
                total_credit+=credit
                total_debit+=debit
                total_amount_currency+=amount_currency
                total_negative_amount_currency+=negative_amount_currency

                line_ids.append((0, 0, {
                                             'name': line.ref,
                                             'account_id': line.account_under_collection_id.id,
                                             'partner_id': self.partner_id.id,
                    'partner_to_id':self.partner_to_id and self.partner_to_id.id or False,

                    'currency_id': currency,
                                             'amount_currency': amount_currency,
                                             'credit': debit,
                                             'debit': credit,
                                             'date_maturity': line.date,
                    'chemical_bank_id':line.chemical_bank_id.id,
                    'bank_id': line.bank_id.id,

                }))
                line_ids.append((0, 0, {
                    'name': line.ref,
                    'account_id': line.account_note_paper_id.id,
                    'partner_id': self.partner_id.id,
                    'partner_to_id':self.partner_to_id and self.partner_to_id.id or False,

                    'currency_id': currency,
                    'amount_currency': amount_currency,
                    'credit': credit,
                    'debit': debit,
                    'date_maturity': line.date,
                    'chemical_bank_id': line.chemical_bank_id.id,
                    'bank_id': line.bank_id.id,

                }))

            created_obj= account_move_obj.create({'name': self.name, 'ref': self.ref,
                                         'journal_id': self.journal_id.id,
                                         'line_ids': line_ids, 'date': self.date})

            created_obj.action_post()
            return True
        if self.journal_id.journal_state == 'return':
            total_debit = 0
            total_credit = 0
            total_amount_currency = 0
            total_negative_amount_currency = 0
            line_ids = []

            for line in self.line_ids:
                if not line.account_under_collection_id:
                    raise UserError(_('You must enter account_note_paper_id account'))
                amount1 = line.amount
                credit = line.amount
                debit = 0.0
                if self.journal_id.currency_id.id != self.env.user.company_id.currency_id.id:
                    jr_rate = self.journal_id.currency_id.rate or 1
                    print("wwwwwwwwwwwwwww", jr_rate)
                    debit = debit * jr_rate if jr_rate >= 1 else debit / jr_rate
                    credit = credit * jr_rate if jr_rate >= 1 else credit / jr_rate
                    print('ooooooooooooooooooooooooooooo', debit, credit)

                if self.not_company_currency:
                    print("uuuuuuuuuuuuuuuuuuuuuu")
                    currency = self.currency_id.id
                    if not self._context.get('return_item'):
                        amount_currency = amount1  # credit / self.custom_rate if self.custom_rate > 1 else credit * self.custom_rate
                        negative_amount_currency = amount1 * -1  # (credit / self.custom_rate if self.custom_rate > 1 else credit * self.custom_rate) * -1
                    else:
                        negative_amount_currency = amount1 * -1  # (debit / self.custom_rate if self.custom_rate > 1 else debit * self.custom_rate) * -1
                        amount_currency = amount1  # (debit / self.custom_rate if self.custom_rate > 1 else debit * self.custom_rate)
                else:
                    currency = False
                    negative_amount_currency = 0
                    amount_currency = 0
                total_credit += credit
                total_debit += debit
                total_amount_currency += amount_currency
                total_negative_amount_currency += negative_amount_currency

                line_ids.append((0, 0, {
                    'name': line.ref,
                    'account_id': line.account_note_paper_id.id,
                    'partner_to_id':self.partner_to_id and self.partner_to_id.id or False,

                    'partner_id': self.partner_id.id,
                    'currency_id': currency,
                    'amount_currency': amount_currency,
                    'credit': debit,
                    'debit': credit,
                    'date_maturity': line.date,
                    'chemical_bank_id': line.chemical_bank_id.id,
                    'bank_id': line.bank_id.id,

                }))
                line_ids.append((0, 0, {
                    'name': line.ref,
                    'account_id': line.account_under_collection_id.id,
                    'partner_to_id':self.partner_to_id and self.partner_to_id.id or False,

                    'partner_id': self.partner_id.id,
                    'currency_id': currency,
                    'amount_currency': amount_currency,
                    'credit': credit,
                    'debit': debit,
                    'date_maturity': line.date,
                    'chemical_bank_id': line.chemical_bank_id.id,
                    'bank_id': line.bank_id.id,

                }))

            created_obj = account_move_obj.create({'name': self.name, 'ref': self.ref,
                                                   'journal_id': self.journal_id.id,
                                                   'line_ids': line_ids, 'date': self.date})

            created_obj.action_post()
            return True

        if self.journal_id.journal_state == 'return_client':
            total_debit=0
            total_credit=0
            total_amount_currency=0
            total_negative_amount_currency=0
            line_ids = []
            line_name=''
            for line in self.line_ids:
                if not line.account_note_paper_id:
                    raise UserError(_('You must enter account_note_paper_id account'))
                amount1 = line.amount
                credit=line.amount
                debit=0.0
                if self.journal_id.currency_id.id != self.env.user.company_id.currency_id.id:
                    jr_rate = self.journal_id.currency_id.rate or 1
                    print("wwwwwwwwwwwwwww", jr_rate)
                    debit = debit * jr_rate if jr_rate >= 1 else debit / jr_rate
                    credit = credit * jr_rate if jr_rate >= 1 else credit / jr_rate
                    print('ooooooooooooooooooooooooooooo', debit, credit)

                if self.not_company_currency:
                    print("uuuuuuuuuuuuuuuuuuuuuu")
                    currency = self.currency_id.id
                    if not self._context.get('return_item'):
                        amount_currency = amount1  # credit / self.custom_rate if self.custom_rate > 1 else credit * self.custom_rate
                        negative_amount_currency = amount1 * -1  # (credit / self.custom_rate if self.custom_rate > 1 else credit * self.custom_rate) * -1
                    else:
                        negative_amount_currency = amount1 * -1  # (debit / self.custom_rate if self.custom_rate > 1 else debit * self.custom_rate) * -1
                        amount_currency = amount1  # (debit / self.custom_rate if self.custom_rate > 1 else debit * self.custom_rate)
                else:
                    currency = False
                    negative_amount_currency = 0
                    amount_currency = 0
                total_credit+=credit
                total_debit+=debit
                total_amount_currency+=amount_currency
                total_negative_amount_currency+=negative_amount_currency
                line_name+='- '+line.ref

                line_ids.append((0, 0, {
                                             'name': line.ref,
                                             'account_id': line.account_note_paper_id.id,
                                             'partner_id': self.partner_id.id,
                    'partner_to_id':self.partner_to_id and self.partner_to_id.id or False,

                    'currency_id': currency,
                                             'amount_currency': negative_amount_currency,
                                             'credit': credit,
                                             'debit': debit,
                                             'date_maturity': line.date,
                    'chemical_bank_id':line.chemical_bank_id.id,
                    'bank_id': line.bank_id.id,

                }))
            line_ids.append((0, 0, {
                    'name': line_name,
                    'account_id': self.partner_id.property_account_receivable_id.id,
                    'partner_id': self.partner_id.id,
                'partner_to_id':self.partner_to_id and self.partner_to_id.id or False,

                'currency_id': currency,
                    'amount_currency': total_negative_amount_currency,
                    'credit': total_debit,
                    'debit': total_credit,
                    'date_maturity': line.date,
                'chemical_bank_id': line.chemical_bank_id.id,
                'bank_id': line.bank_id.id,
                }))
            created_obj= account_move_obj.create({'name': self.name, 'ref': self.ref,
                                         'journal_id': self.journal_id.id,
                                         'line_ids': line_ids, 'date': self.date})

            created_obj.action_post()
            return True




        if self.journal_id.journal_state == 'collect':
            total_debit=0
            total_credit=0
            total_amount_currency=0
            total_negative_amount_currency=0
            line_ids = []
            line_name=''
            for line in self.line_ids:
                if not line.account_bank_collect_id:
                    raise UserError(_('You must enter account_bank_collect_id account'))
                amount1 = line.amount
                credit=line.amount
                debit=0.0
                if self.journal_id.currency_id.id != self.env.user.company_id.currency_id.id:
                    jr_rate = self.journal_id.currency_id.rate or 1
                    print("wwwwwwwwwwwwwww", jr_rate)
                    debit = debit * jr_rate if jr_rate >= 1 else debit / jr_rate
                    credit = credit * jr_rate if jr_rate >= 1 else credit / jr_rate
                    print('ooooooooooooooooooooooooooooo', debit, credit)

                if self.not_company_currency:
                    print("uuuuuuuuuuuuuuuuuuuuuu")
                    currency = self.currency_id.id
                    if not self._context.get('return_item'):
                        amount_currency = amount1  # credit / self.custom_rate if self.custom_rate > 1 else credit * self.custom_rate
                        negative_amount_currency = amount1 * -1  # (credit / self.custom_rate if self.custom_rate > 1 else credit * self.custom_rate) * -1
                    else:
                        negative_amount_currency = amount1 * -1  # (debit / self.custom_rate if self.custom_rate > 1 else debit * self.custom_rate) * -1
                        amount_currency = amount1  # (debit / self.custom_rate if self.custom_rate > 1 else debit * self.custom_rate)
                else:
                    currency = False
                    negative_amount_currency = 0
                    amount_currency = 0
                total_credit+=credit
                total_debit+=debit
                total_amount_currency+=amount_currency
                total_negative_amount_currency+=negative_amount_currency
                line_name+='- '+line.ref
                line_ids.append((0, 0, {
                                             'name': line.ref,
                                             'account_id': line.account_bank_collect_id.id,
                                             'partner_id': self.partner_id.id,
                    'partner_to_id':self.partner_to_id and self.partner_to_id.id or False,

                    'currency_id': currency,
                                             'amount_currency': amount_currency,
                                             'credit': debit,
                                             'debit': credit,
                                             'date_maturity': line.date,
                    'chemical_bank_id':line.chemical_bank_id.id,
                    'bank_id': line.bank_id.id,

                }))
                line_ids.append((0, 0, {
                    'name': line_name,
                    'account_id': line.account_under_collection_id.id,
                    'partner_id': self.partner_id.id,
                    'partner_to_id':self.partner_to_id and self.partner_to_id.id or False,

                    'currency_id': currency,
                    'amount_currency': amount_currency,
                    'credit': credit,
                    'debit': debit,
                    'date_maturity': line.date,
                    'chemical_bank_id': line.chemical_bank_id.id,
                    'bank_id': line.bank_id.id,

                }))

            created_obj= account_move_obj.create({'name': self.name, 'ref': self.ref,
                                         'journal_id': self.journal_id.id,
                                         'line_ids': line_ids, 'date': self.date})

            created_obj.action_post()
            return True

        if self.journal_id.journal_state == 'generate_supp':
            total_debit=0
            total_credit=0
            total_amount_currency=0
            total_negative_amount_currency=0
            line_ids = []

            for line in self.line_ids:
                if not line.generate_check_to_supplier:
                    raise UserError(_('You must enter generate_check_to_supplier account'))
                amount1 = line.amount
                credit=line.amount
                debit=0.0
                if self.journal_id.currency_id.id != self.env.user.company_id.currency_id.id:
                    jr_rate = self.journal_id.currency_id.rate or 1
                    print("wwwwwwwwwwwwwww", jr_rate)
                    debit = debit * jr_rate if jr_rate >= 1 else debit / jr_rate
                    credit = credit * jr_rate if jr_rate >= 1 else credit / jr_rate
                    print('ooooooooooooooooooooooooooooo', debit, credit)

                if self.not_company_currency:
                    print("uuuuuuuuuuuuuuuuuuuuuu")
                    currency = self.currency_id.id
                    if not self._context.get('return_item'):
                        amount_currency = amount1  # credit / self.custom_rate if self.custom_rate > 1 else credit * self.custom_rate
                        negative_amount_currency = amount1 * -1  # (credit / self.custom_rate if self.custom_rate > 1 else credit * self.custom_rate) * -1
                    else:
                        negative_amount_currency = amount1 * -1  # (debit / self.custom_rate if self.custom_rate > 1 else debit * self.custom_rate) * -1
                        amount_currency = amount1  # (debit / self.custom_rate if self.custom_rate > 1 else debit * self.custom_rate)
                else:
                    currency = False
                    negative_amount_currency = 0
                    amount_currency = 0
                total_credit+=credit
                total_debit+=debit
                total_amount_currency+=amount_currency
                total_negative_amount_currency+=negative_amount_currency

                line_ids.append((0, 0, {
                                             'name': line.ref,
                                             'account_id':  self.partner_id.property_account_payable_id.id,
                                             'partner_id': self.partner_id.id,
                                             'currency_id': currency,
                                             'amount_currency': amount_currency,
                                             'credit': debit,
                                             'debit': credit,
                                             'date_maturity': line.date,
                    'chemical_bank_id':line.chemical_bank_id.id,
                    'bank_id': line.bank_id.id,

                }))
            line_ids.append((0, 0, {
                    'name': line.ref,
                    'account_id': line.generate_check_to_supplier.id,
                    'partner_id': self.partner_id.id,
                    'currency_id': currency,
                    'amount_currency': total_negative_amount_currency,
                    'credit': total_credit,
                    'debit': total_debit,
                    'date_maturity': line.date,
                'chemical_bank_id': line.chemical_bank_id.id,
                'bank_id': line.bank_id.id,
                }))
            created_obj= account_move_obj.create({'name': self.name, 'ref': self.ref,
                                         'journal_id': self.journal_id.id,
                                         'line_ids': line_ids, 'date': self.date})

            created_obj.action_post()
            return True

        if self.journal_id.journal_state == 'bank_payment':
            total_debit=0
            total_credit=0
            total_amount_currency=0
            total_negative_amount_currency=0
            line_ids = []

            for line in self.line_ids:
                if not line.bank_payment:
                    raise UserError(_('You must enter bank_payment account'))
                amount1 = line.amount
                credit=line.amount
                debit=0.0
                if self.journal_id.currency_id.id != self.env.user.company_id.currency_id.id:
                    jr_rate = self.journal_id.currency_id.rate or 1
                    print("wwwwwwwwwwwwwww", jr_rate)
                    debit = debit * jr_rate if jr_rate >= 1 else debit / jr_rate
                    credit = credit * jr_rate if jr_rate >= 1 else credit / jr_rate
                    print('ooooooooooooooooooooooooooooo', debit, credit)

                if self.not_company_currency:
                    print("uuuuuuuuuuuuuuuuuuuuuu")
                    currency = self.currency_id.id
                    if not self._context.get('return_item'):
                        amount_currency = amount1  # credit / self.custom_rate if self.custom_rate > 1 else credit * self.custom_rate
                        negative_amount_currency = amount1 * -1  # (credit / self.custom_rate if self.custom_rate > 1 else credit * self.custom_rate) * -1
                    else:
                        negative_amount_currency = amount1 * -1  # (debit / self.custom_rate if self.custom_rate > 1 else debit * self.custom_rate) * -1
                        amount_currency = amount1  # (debit / self.custom_rate if self.custom_rate > 1 else debit * self.custom_rate)
                else:
                    currency = False
                    negative_amount_currency = 0
                    amount_currency = 0
                total_credit+=credit
                total_debit+=debit
                total_amount_currency+=amount_currency
                total_negative_amount_currency+=negative_amount_currency

                line_ids.append((0, 0, {
                                             'name': line.ref,
                                             'account_id': line.generate_check_to_supplier.id,
                                             'partner_id': self.partner_id.id,
                                             'currency_id': currency,
                                             'amount_currency': amount_currency,
                                             'credit': debit,
                                             'debit': credit,
                                             'date_maturity': line.date,
                    'chemical_bank_id':line.chemical_bank_id.id,
                    'bank_id': line.bank_id.id,

                }))
                line_ids.append((0, 0, {
                    'name': line.ref,
                    'account_id': line.bank_payment.id,
                    'partner_id': self.partner_id.id,
                    'currency_id': currency,
                    'amount_currency': amount_currency,
                    'credit': credit,
                    'debit': debit,
                    'date_maturity': line.date,
                    'chemical_bank_id': line.chemical_bank_id.id,
                    'bank_id': line.bank_id.id,

                }))

            created_obj= account_move_obj.create({'name': self.name, 'ref': self.ref,
                                         'journal_id': self.journal_id.id,
                                         'line_ids': line_ids, 'date': self.date})

            created_obj.action_post()
            return True
        if self.journal_id.journal_state == 'cheque_return':
            total_debit=0
            total_credit=0
            total_amount_currency=0
            total_negative_amount_currency=0
            line_ids = []

            for line in self.line_ids:
                if not line.generate_check_to_supplier:
                    raise UserError(_('You must enter generate_check_to_supplier account'))
                amount1 = line.amount
                credit=line.amount
                debit=0.0
                if self.journal_id.currency_id.id != self.env.user.company_id.currency_id.id:
                    jr_rate = self.journal_id.currency_id.rate or 1
                    print("wwwwwwwwwwwwwww", jr_rate)
                    debit = debit * jr_rate if jr_rate >= 1 else debit / jr_rate
                    credit = credit * jr_rate if jr_rate >= 1 else credit / jr_rate
                    print('ooooooooooooooooooooooooooooo', debit, credit)

                if self.not_company_currency:
                    print("uuuuuuuuuuuuuuuuuuuuuu")
                    currency = self.currency_id.id
                    if not self._context.get('return_item'):
                        amount_currency = amount1  # credit / self.custom_rate if self.custom_rate > 1 else credit * self.custom_rate
                        negative_amount_currency = amount1 * -1  # (credit / self.custom_rate if self.custom_rate > 1 else credit * self.custom_rate) * -1
                    else:
                        negative_amount_currency = amount1 * -1  # (debit / self.custom_rate if self.custom_rate > 1 else debit * self.custom_rate) * -1
                        amount_currency = amount1  # (debit / self.custom_rate if self.custom_rate > 1 else debit * self.custom_rate)
                else:
                    currency = False
                    negative_amount_currency = 0
                    amount_currency = 0
                total_credit+=credit
                total_debit+=debit
                total_amount_currency+=amount_currency
                total_negative_amount_currency+=negative_amount_currency

                line_ids.append((0, 0, {
                                             'name': line.ref,
                                             'account_id': self.partner_id.property_account_payable_id.id,
                                             'partner_id': self.partner_id.id,
                                             'currency_id': currency,
                                             'amount_currency': negative_amount_currency,
                                             'credit': credit,
                                             'debit': debit,
                                             'date_maturity': line.date,
                    'chemical_bank_id':line.chemical_bank_id.id,
                    'bank_id': line.bank_id.id,

                }))
                line_ids.append((0, 0, {
                        'name': line.ref,
                        'account_id': line.generate_check_to_supplier.id,
                        'partner_id': self.partner_id.id,
                        'currency_id': currency,
                        'amount_currency': negative_amount_currency,
                        'credit': debit,
                        'debit': credit,
                        'date_maturity': line.date,
                    'chemical_bank_id': line.chemical_bank_id.id,
                    'bank_id': line.bank_id.id,
                    }))
            created_obj= account_move_obj.create({'name': self.name, 'ref': self.ref,
                                         'journal_id': self.journal_id.id,
                                         'line_ids': line_ids, 'date': self.date})

            created_obj.action_post()
            return True

        return True

    def close(self):
        self.write({'state':'confirm'})

    def button_receive(self):
        if self.journal_id.journal_state!='receive':
            raise UserError(_('You can not use this Journal for that state'))
        self.check_move_create()
        self.write({'state':'receive'})

    def button_deposit_check(self):
        if self.journal_id.journal_state!='deposit':
            raise UserError(_('You can not use this Journal for that state'))
        self.check_move_create()
        self.write({'state':'deposit'})

    def button_collect_check(self):
        if self.journal_id.journal_state!='collect':
            raise UserError(_('You can not use this Journal for that state'))
        self.check_move_create()
        self.write({'state':'collect'})

    def button_bnk_return_check(self):
        if self.journal_id.journal_state!='return':
            raise UserError(_('You can not use this Journal for that state'))
        self.check_move_create()
        self.write({'state':'return'})

    def button_return_client_check(self):
        if self.journal_id.journal_state!='return_client':
            raise UserError(_('You can not use this Journal for that state'))
        self.check_move_create()
        self.write({'state':'return_client'})

    def button_direct_deposit(self):
        if self.journal_id.journal_state!='deposit_direct':
            raise UserError(_('You can not use this Journal for that state'))
        self.check_move_create(0.0,self.amount)
        self.write({'state':'deposit_direct'})

    def button_generate_chk_supp(self):
        if self.journal_id.journal_state!='generate_supp':
            raise UserError(_('You can not use this Journal for that state'))
        self.check_move_create()
        self.write({'state':'generate_supp'})

    def button_bnk_payment(self):
        if self.journal_id.journal_state!='bank_payment':
            raise UserError(_('You can not use this Journal for that state'))
        self.check_move_create()
        self.write({'state':'bank_payment'})


    # llllllllllllllllllllllllllllllllllll
    def button_pay_bnk_return_check(self):
        if self.journal_id.journal_state!='cheque_return':
            raise UserError(_('You can not use this Journal for that state'))
        self.check_move_create()
        self.write({'state':'cheque_return'})


    def button_check_hashed(self):
        if self.journal_id.journal_state!='cheque_hashed':
            raise UserError(_('You can not use this Journal for that state'))
        # self.check_move_create(0.0,self.amount)
        self.write({'state':'cheque_hashed'})

        wizard_form = self.env.ref('itsys_account_check.hash_to_supplier_wiz_form', False)
        view_id = self.env['check.hash.supplier']

        # new = view_id.create({})
        return {
            'name': _('Choose Vendor'),
            'type': 'ir.actions.act_window',
            'res_model': 'check.hash.supplier',
            # 'res_id': new.id,
            'view_id': wizard_form.id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new'
        }

    def button_return_check_hashed(self):
        if self.journal_id.journal_state!='return_cheque_hashed':
            raise UserError(_('You can not use this Journal for that state'))
        self.check_move_create(0.0,self.amount)
        self.write({'state':'return_cheque_hashed','supplier_id':False})

    def button_client_return_check(self):
        if self.journal_id.journal_state != 'return_client':
            raise UserError(_('You can not use this Journal for that state'))
        self.check_move_create(self.amount, 0.0)
        self.write({'state': 'return_client'})

    @api.onchange('account_under_collection_id')
    def onchange_ref(self):
        for rec in self:
            for each in rec.line_ids:
                if rec.account_under_collection_id:
                    each.account_under_collection_id = rec.account_under_collection_id

    @api.onchange('account_bank_collect_id')
    def onchange_refaccount_bank_collect_id(self):
        for rec in self:
            for each in rec.line_ids:
                if rec.account_bank_collect_id:
                    each.account_bank_collect_id = rec.account_bank_collect_id

    @api.onchange('generate_check_to_supplier')
    def onchange_generate_check_to_supplier(self):
        for rec in self:
            for each in rec.line_ids:
                if rec.generate_check_to_supplier:
                    each.generate_check_to_supplier = rec.generate_check_to_supplier
    @api.onchange('bank_payment')
    def onchange_bank_payment(self):
        for rec in self:
            for each in rec.line_ids:
                if rec.bank_payment:
                    each.bank_payment = rec.bank_payment

class CheckLines(models.Model):
    _name = 'check.lines'
    _rec_name='ref'
    _order = 'id desc'
    @api.model
    def create(self, vals):
        if self._context.get('default_collect_ok'):
            vals['check_type']='collect'
        else:
            vals['check_type']='pay'
        return super(CheckLines, self).create(vals)
    @api.model
    def _default_state(self):

        if self._context.get('default_collect_ok'):
            return 'draft_collect'
        else:
            return 'draft_pay'
    # @api.model
    # def _default_type(self):
    #     print('self._context',self.check_id.collect_ok)
    #     if self.check_id.collect_ok:
    #         return 'collect'
    #     else:
    #         return 'pay'

    check_type = fields.Selection([('collect', 'Collect'),
                              ('pay', 'Pay'),
                              ],
                             string='Type', required=True,
                             copy=False, )
    ref = fields.Char('Reference',required=True)
    amount = fields.Float('Amount')
    date = fields.Date('Due Date',required=True)
    comm = fields.Char('Communication')
    check_id = fields.Many2one('account.check', string='account check')
    chemical_bank_id=fields.Many2one('chemical.bank',string='Chemical Bank')
    bank_id=fields.Many2one('chemical.bank',string='Bank')
    account_note_paper_id = fields.Many2one('account.account', string='Note Paper')
    account_under_collection_id = fields.Many2one('account.account', string='Check under collection')
    account_bank_collect_id = fields.Many2one('account.account', string='Bank Collect')
    generate_check_to_supplier = fields.Many2one('account.account', string='Generate check to supplier')
    bank_payment = fields.Many2one('account.account', string='Bank Payment')

    state = fields.Selection([('draft_collect', 'New'),
                              ('draft_pay', 'pay'),
                              ('open', 'Open'),
                              ('receive', 'Paper Receive'),
                              ('deposit', 'Bank Deposit'),
                              ('collect', 'Collect Cheque'),
                              ('return', 'Return Check'),
                              ('cash_payment', 'Cash Payment'),
                              ('return_client', 'Return to Client'),
                              ('cheque_hashed', 'Hash cheque to supplier'),
                              ('return_cheque_hashed', 'Return hashed cheque to supplier'),
                              ('deposit_direct', 'Direct Deposit'),
                              ('generate_supp', 'Generate Cheque - Supplier'),
                              ('bank_payment', 'Bank Payment'),
                              ('cheque_return', 'Cheque Return from bank'),
                              ('confirm', 'Closed'),
                              ('cancel', 'Cancel'), ], related='check_id.state',
                             string='Status', required=True, default=_default_state, readonly="1",
                             copy=False, )

    @api.constrains('amount')
    def check_mount(self):
        for rec in self:
            if rec.amount <= 0.0:
                raise UserError(_('Error ! Amount cannot be zero or less '))
    @api.onchange('ref')
    def onchange_ref(self):
        print('self._context',self._context.get('default_collect_ok'))

        for rec in self:
            # if self._context.get('default_collect_ok'):
            #     print('ffff')
            #     rec.check_type='collect'
            # else:
            #     rec.check_type='pay'

            if rec.check_id.account_note_paper_id:
                rec.account_note_paper_id=rec.check_id.account_note_paper_id
            if rec.check_id.account_under_collection_id:
                rec.account_under_collection_id=rec.check_id.account_under_collection_id


            if rec.check_id.generate_check_to_supplier:
                rec.generate_check_to_supplier=rec.check_id.generate_check_to_supplier
            if rec.check_id.bank_payment:
                rec.bank_payment=rec.check_id.bank_payment


class account_journal(models.Model):
    _inherit = 'account.journal'
    journal_state = fields.Selection(
        [('receive', 'Receive')
            , ('deposit', 'Deposit')
            , ('collect', 'Collect')
            , ('return', 'Return')
            , ('return_client', 'Return to Client')
            , ('deposit_direct', 'Direct deposit')
            , ('generate_exp', 'Generate check-Expenses')
            , ('generate_supp', 'Generate check-Supplier')
            , ('bank_payment', 'Bank Payment'),
         ('cheque_return', 'Cheque Return from bank'),
         ('cheque_hashed', 'Hash chk to supplier'),
         ('return_cheque_hashed', 'Return hashed chk to supplier'),
         ], 'Check Journal State', help="Select the tybe of journal to deal with bank checks")
    bnk_payable = fields.Boolean('Bank Payable')
    bnk_receive = fields.Boolean('Bank Receive')

class ChemicalPartnerBank(models.Model):
    _name = 'chemical.bank'
    _rec_name = 'name'

    name = fields.Char('Bank Name',required=True)

class accountmoveline(models.Model):
    _inherit = 'account.move.line'

    chemical_bank_id=fields.Many2one('chemical.bank',string='Chemical Bank')
    bank_id=fields.Many2one('chemical.bank',string='Bank')
    check_id = fields.Many2one('account.check', string='account check')
    partner_to_id = fields.Many2one('res.partner', string='Customer to')
