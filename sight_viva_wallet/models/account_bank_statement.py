# coding: utf-8
from odoo import api, fields, models, _



class StatementLine(models.Model):

    _inherit = 'account.bank.statement.line'

    viva_trx = fields.Char('Viva Transaction')
