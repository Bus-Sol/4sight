# -*- coding: utf-8 -*-
import logging
from odoo import models, api, _
from odoo.exceptions import UserError
import hashlib
import uuid

from datetime import datetime

_logger = logging.getLogger(__name__)

class ResUsers(models.Model):
    _inherit = 'res.users'

    def generate_token_for_portal(self, user_id, email):
        profile_uuid = self.env['ir.config_parameter'].sudo().get_param('portal_user.uuid')
        if not profile_uuid:
            profile_uuid = str(uuid.uuid4())
            self.env['ir.config_parameter'].sudo().set_param('portal_user.uuid', profile_uuid)
        return hashlib.sha256((u'%s-%s-%s-%s' % (
            datetime.now().replace(day=4, hour=0, minute=0, second=0, microsecond=0),
            profile_uuid,
            user_id,
            email
        )).encode('utf-8')).hexdigest()

    # def action_reset_password(self):
    #     """ create signup token for each user, and send their signup url by email """
    #     if self.env.context.get('install_mode', False):
    #         return
    #     if self.filtered(lambda user: not user.active):
    #         raise UserError(_("You cannot perform this action on an archived user."))
    #     # prepare reset password signup
    #     create_mode = bool(self.env.context.get('create_user'))
    #     create_mode_ticket = bool(self.env.context.get('create_user_without_pwd'))
    #
    #     # no time limit for initial invitation, only for reset password
    #     expiration = False if create_mode else now(days=+1)
    #
    #     self.mapped('partner_id').signup_prepare(signup_type="reset", expiration=expiration)
    #
    #     # send email to users with their signup url
    #     template = False
    #     if create_mode:
    #         try:
    #             template = self.env.ref('auth_signup.set_password_email', raise_if_not_found=False)
    #         except ValueError:
    #             pass
    #     if create_mode_ticket:
    #         try:
    #             template = self.env['mail.template'].browse(10)
    #         except ValueError:
    #             pass
    #     if not template:
    #         template = self.env.ref('auth_signup.reset_password_email')
    #     assert template._name == 'mail.template'
    #
    #     template_values = {
    #         'email_to': '${object.email|safe}',
    #         'email_cc': False,
    #         'auto_delete': True,
    #         'partner_to': False,
    #         'scheduled_date': False,
    #     }
    #     template.write(template_values)
    #
    #     for user in self:
    #         if not user.email:
    #             raise UserError(_("Cannot send email: user %s has no email address.", user.name))
    #         # TDE FIXME: make this template technical (qweb)
    #         with self.env.cr.savepoint():
    #             force_send = not(self.env.context.get('import_file', False))
    #             template.send_mail(user.id, force_send=force_send, raise_exception=True)
    #         _logger.info("Password reset email sent for user <%s> to <%s>", user.login, user.email)
