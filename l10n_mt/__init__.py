# -*- coding: utf-8 -*-

from odoo import api, SUPERUSER_ID
from . import models
from . import controllers


def pre_init_check(cr):

    env = api.Environment(cr, SUPERUSER_ID, {})
    installer = env['base.language.install'].create({'lang': 'en_GB'})
    installer.lang_install()
    users = env['res.users'].search([])
    for user in users:
        user.write({'tz': 'Europe/Malta','lang':'en_GB'})

    payment_terms = env['account.payment.term'].search([])
    if not env['account.move'].search([('invoice_payment_term_id', 'in', payment_terms.ids)]):
        for payment_term in payment_terms:
            try:
                payment_term.unlink()
            except ValueError:
                pass

    reconciles = env['account.reconcile.model'].search([])
    for reconcile in reconciles:
        reconcile.unlink()

