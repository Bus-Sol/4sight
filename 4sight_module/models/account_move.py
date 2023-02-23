# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = "account.move"

    #tax_closing_start_date = fields.Date(help="Technical field used for VAT closing, containig the start date of the period this entry closes.")
    tax_closing_date_from = fields.Date()
    tax_closing_date_to = fields.Date()