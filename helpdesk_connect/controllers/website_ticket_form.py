# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
import json
from psycopg2 import IntegrityError
from odoo.exceptions import ValidationError, UserError
from odoo.addons.website.controllers import form


class WebsiteForm(form.WebsiteForm):
    def _handle_website_form(self, model_name, **kwargs):
            model_record = request.env['ir.model'].sudo().search(
                [('model', '=', model_name), ('website_form_access', '=', True)])
            if not model_record:
                return json.dumps({
                    'error': _("The form's specified model does not exist")
                })

            try:
                data = self.extract_data(model_record, request.params)
            # If we encounter an issue while extracting data
            except ValidationError as e:
                # I couldn't find a cleaner way to pass data to an exception
                return json.dumps({'error_fields': e.args[0]})

            try:
                if model_record.model == 'helpdesk.ticket':
                    data['record']['phone'] = kwargs['phone']
                    data['record']['company_name'] = kwargs['company_name']
                    data['custom'] = ''
                id_record = self.insert_record(request, model_record, data['record'], data['custom'], data.get('meta'))
                if id_record:
                    self.insert_attachment(model_record, id_record, data['attachments'])
                    # in case of an email, we want to send it immediately instead of waiting
                    # for the email queue to process
                    if model_name == 'mail.mail':
                        request.env[model_name].sudo().browse(id_record).send()

            # Some fields have additional SQL constraints that we can't check generically
            # Ex: crm.lead.probability which is a float between 0 and 1
            # TODO: How to get the name of the erroneous field ?
            except IntegrityError:
                return json.dumps(False)

            request.session['form_builder_model_model'] = model_record.model
            request.session['form_builder_model'] = model_record.name
            request.session['form_builder_id'] = id_record

            return json.dumps({'id': id_record})