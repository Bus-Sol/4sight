# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"


    def create_invoices(self):
        """ Override method from sale/wizard/sale_make_invoice_advance.py"""

        sale_orders = self.env['sale.order'].browse(
            self._context.get('active_ids', [])
        )

        if self.advance_payment_method == 'delivered':
            lead_ids = sale_orders.mapped('opportunity_id')
            print("+++++++++++++lead_ids____________________",lead_ids)
            for lead in lead_ids:
                lead.stage_id= lead._stage_find(domain=['|',('fold', '=', True),('fold', '=', False)]).id
                print("+++++++++++++++++lead.satge_id++++++++++++++++++",lead.stage_id)
            sale_orders._create_invoices(final=self.deduct_down_payments)


            if self._context.get('open_invoices', False):
                return sale_orders.action_view_invoice()
            return {'type': 'ir.actions.act_window_close'}

        return super(SaleAdvancePaymentInv, self).create_invoices()