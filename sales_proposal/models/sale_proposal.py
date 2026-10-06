# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SalesInheritProposal(models.Model):
    _inherit = 'sale.order'

    sales_proposal_count = fields.Integer(compute='_compute_sales_proposal_count')
    

    def sales_proposal_button(self):
        quotation_proposal = self.env['proposal.proposal'].search([('sale_id', '=', self.name)])
        return {
            'type': 'ir.actions.act_window',
            'name': 'Proposal',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'proposal.proposal',
            'domain': [('id', 'in', quotation_proposal.ids)]

        }
    def _compute_sales_proposal_count(self):
        self.sales_proposal_count = self.env['proposal.proposal'].search_count([('sale_id', '=', self.name)])
        print("Count:",self.sales_proposal_count)

class ProposalProposal(models.Model):
    _name = 'proposal.proposal'
    _description = 'Sale Proposal'

    name = fields.Char(string='Proposal Name')
    page_ids = fields.One2many('proposal.page.line','proposal_id',string='Pages')
    date = fields.Date(string='Proposal Date')
    include_quote = fields.Boolean(string='Include Quotation')
    ref = fields.Char(string='Ref No')
    sale_id = fields.Many2one('sale.order', string="Related Quotation" ,domain="[('state', 'not in',('sale','done'))]")

    _sql_constraints = [
        ("proposal_ref_unique", "UNIQUE(ref)", "Proposal Ref No must be unique!")
    ]
    @api.onchange('include_quote')
    def _onchange_quotation(self):
        if self.include_quote == True:
            self.include_quotation()

    def include_quotation(self):
        page_ids = []
        terms_obj = self.env['proposal.page']
        termsids = terms_obj.search([])
        for rec in termsids:
            if rec.name == 'Quotation':
                page_ids.append((0, 0,{'page_id':rec.id}))
        res = super(ProposalProposal, self)
        res.update({'page_ids': page_ids})
        return res

    @api.model
    def create(self, vals):
        terms_obj = self.env['proposal.page']
        termsids = terms_obj.search([])
        for rec in termsids:
            if rec.name == 'Quotation':
                rec.is_quotation = True
        vals['ref'] = self.env['ir.sequence'].next_by_code('proposal.proposal') or '/'
        return super(ProposalProposal, self).create(vals)

    def send_sale_proposals(self):
        for rec in self:
            if rec.sale_id:
                # template_id = self.env['ir.model.data']._xmlid_to_res_id('sales_proposal.sale_proposal_email_template', raise_if_not_found=False)
                template_id = self.env.ref('sales_proposal.sale_proposal_email_template', False)
                template = self.env['mail.template'].browse(template_id)
                ctx = {
                    'default_model': 'proposal.proposal',
                    'default_res_id': self.ids[0],
                    'default_use_template': bool(template_id.id),
                    'default_template_id': template_id.id,
                    'default_composition_mode': 'comment',
                    'custom_layout': 'mail.mail_notification_light',
                    'force_email': True,

                }
                return {
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'mail.compose.message',
                    'views': [(False, 'form')],
                    'view_id': False,
                    'target': 'new',
                    'context': ctx,
                }
            if not rec.sale_id:
                raise ValidationError("Please select the Related Quotation.")


class ProposalPagesLine(models.Model):
    _name = 'proposal.page.line'

    proposal_id = fields.Many2one('proposal.proposal', string="Proposal")
    page_id = fields.Many2one('proposal.page', string="Pages")
    sequence = fields.Integer(string='Sequence', default=10)


class ProposalPages(models.Model):
    _name = 'proposal.page'

    name = fields.Char(string='Page Name')
    description = fields.Html(string='Description')
    is_quotation = fields.Boolean(string="order", default = False)
    quotation = fields.Boolean(string="quotation", default = True)





