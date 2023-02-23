# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _


class ResCompany(models.Model):
    _inherit = "res.company"
    def _create_edit_tax_reminder(self, in_period_date, create_when_empty=False):
        self.ensure_one()

        if self._context.get('no_create_move', False):
            return self.env['account.move']
        if not create_when_empty and not self.env['account.tax.group']._any_is_configured(self):
            return False

        # Create/Edit activity type if needed
        move_res_model_id = self.env['ir.model'].search([('model', '=', 'account.move')], limit=1).id
        activity_type = self.account_tax_next_activity_type or False
        delay_count = self._get_tax_periodicity_months_delay()
        vals = {
            'category': 'tax_report',
            'delay_count': delay_count,
            'delay_unit': 'months',
            'delay_from': 'previous_activity',
            'res_model_id': move_res_model_id,
            'force_next': False,
        }
        if not activity_type:
            vals.update({
                'name': _('Tax Report for company %s') % (self.name,),
                'summary': _('TAX Report'),
            })
            activity_type = self.env['mail.activity.type'].create(vals)
            self.account_tax_next_activity_type = activity_type
        else:
            activity_type.write(vals)

        # Compute period dates depending on the date
        period_start, period_end = self._get_tax_closing_period_boundaries(in_period_date)
        print(self._context)
        activity_deadline = period_end + relativedelta(days=self.account_tax_periodicity_reminder_day)

        # Search for an existing tax closing move
        tax_closing_move = self.env['account.move'].search([
            ('state', '=', 'draft'),
            ('journal_id', '=', self.account_tax_periodicity_journal_id.id),
            ('activity_ids.activity_type_id', '=', activity_type.id),
            ('tax_closing_end_date', '<=', period_end),
            ('tax_closing_end_date', '>=', period_start)
        ], limit=1)

        # Compute tax closing description
        ref = self._get_tax_closing_move_description(self.account_tax_periodicity, period_start, period_end)

        # Write move
        if tax_closing_move:
            # Update the next activity on the existing move
            for act in tax_closing_move.activity_ids:
                if act.activity_type_id == activity_type:
                    act.write({'date_deadline': activity_deadline})
            tax_closing_move.date = period_end
            tax_closing_move.ref = ref
            tax_closing_move.tax_closing_end_date = period_end
            tax_closing_move.tax_closing_date_from = self._context.get('date_from', False)
            tax_closing_move.tax_closing_date_to = self._context.get('date_to', False)
        else:
            # Create a new, empty, tax closing move
            tax_closing_move = self.env['account.move'].create({
                'journal_id': self.account_tax_periodicity_journal_id.id,
                'date': period_end,
                'tax_closing_end_date': period_end,
                'tax_closing_date_from': self._context.get('date_from', False),
                'tax_closing_date_to': self._context.get('date_to', False),
                'ref': ref,
            })
            advisor_user = self.env['res.users'].search(
                [('company_ids', 'in', (self.id,)), ('groups_id', 'in', self.env.ref('account.group_account_manager').ids)],
                limit=1, order="id ASC")
            activity_vals = {
                'res_id': tax_closing_move.id,
                'res_model_id': move_res_model_id,
                'activity_type_id': activity_type.id,
                'summary': activity_type.summary,
                'note': activity_type.default_description,
                'date_deadline': activity_deadline,
                'automated': True,
                'user_id':  advisor_user.id or self.env.user.id
            }
            self.env['mail.activity'].with_context(mail_activity_quick_update=True).create(activity_vals)

        return tax_closing_move