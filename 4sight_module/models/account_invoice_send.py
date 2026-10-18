# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


# class AccountInvoiceSend(models.TransientModel):
#     _inherit = "account.invoice.send"
#
#     include_followers = fields.Boolean('Include followers', default=True)
#
#     def send_and_print_action(self):
#         if not self.include_followers:
#             self.composer_id.with_context(notify_followers=self.include_followers)
#             new_ctx = self._context.copy()
#             new_ctx.update({'notify_followers': self.include_followers})
#             self = self.with_context(new_ctx)
#
#         return self.send_and_print()

