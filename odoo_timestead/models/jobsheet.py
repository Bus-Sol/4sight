# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from werkzeug.urls import url_encode

class JobSheet(models.Model):
    _name = "client.jobsheet"
    _inherit = ['mail.thread','portal.mixin','timer.mixin','mail.activity.mixin']
    _order = 'id desc'
    _description = "Jobsheet"

    def get_list_partners(self):
        return [('jobsheet_type','!=',False)]

    name = fields.Char('Ref', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    partner_id = fields.Many2one('res.partner', 'Client', domain=get_list_partners)
    service_domain = fields.Many2many('product.template', compute='compute_service_domain')
    service_id = fields.Many2one('product.template', domain="[('id', 'in', service_domain)]")
    user_id = fields.Many2one('res.users', 'User', required=True, default=lambda self: self.env.user)
    brief = fields.Char('Brief')
    date_order = fields.Datetime(string='Date', readonly=True, index=True, default=fields.Datetime.now)
    details = fields.Text(string='Details')
    jobsheet_type_id = fields.Many2one('jobsheet.type', 'Jobsheet Types')
    start_date = fields.Datetime(string='Start')
    jobsheet_start = fields.Date(string='Jobsheet Start', compute='compute_start_job', store=True)
    end_date = fields.Datetime(string='End')
    jobsheet_line = fields.One2many('jobsheet.line', 'jobsheet_id', 'Jobsheet Details')
    status = fields.Selection([('created','Created'),('confirmed', 'Confirmed'),('sent','Email Sent'),('signed','Signed by Client'),('invoiced','Invoiced')], default="created")
    hours = fields.Float('Hours')
    signee = fields.Char('Signee')
    move_ids = fields.Many2many("account.move", string='Moves', compute="_get_invoiced", readonly=True,
                                   copy=False, groups='odoo_timestead.group_jobsheet_manager')
    move_count = fields.Integer(string='Move Count', compute='_get_invoiced', readonly=True)
    signature = fields.Binary(string='Signature',attachment=True)
    category_id = fields.Many2many('jobsheet.tags', column1='jobsheet_id',
                                   column2='category_id', string='Tags')
    overtime = fields.Boolean('Overtime', default=False)
    hours_overtime = fields.Float()
    type = fields.Selection([('postpaid','Postpaid'),('contract','Daily Contract'),('prepaid','Prepaid')], default='contract', string='Type', readonly=1)
    is_prepaid = fields.Boolean(default=True)
    currency_id = fields.Many2one('res.currency', 'Currency', required=True,
                                  default=lambda self: self.env.company.currency_id.id, groups='odoo_timestead.group_jobsheet_manager')
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all', tracking=4)
    company_id = fields.Many2one('res.company', required=True, readonly=True, default=lambda self: self.env.company)
    planned_date_begin = fields.Datetime("Start date")
    planned_date_end = fields.Datetime("End date")
    display_timer_start_secondary = fields.Boolean(compute='_compute_display_timer_buttons')
    project_id = fields.Many2one('project.project', string='Project', help='Project in which to create the task')
    timesheet_ids = fields.One2many('account.analytic.line', 'job_id', 'Timesheets')
    effective_hours = fields.Float("Hours Spent", compute='_compute_effective_hours', compute_sudo=True, store=True,
                                   help="Time spent on this task, excluding its sub-tasks.")
    task_id = fields.Many2one('project.task', compute='compute_task_id', store=True)
    planned_hours = fields.Float(related='task_id.planned_hours')
    remaining_hours = fields.Float(related='task_id.remaining_hours')
    progress = fields.Float(related='task_id.progress')
    sale_order_id = fields.Many2one('sale.order', string='Next Sale Order', groups='odoo_timestead.group_jobsheet_manager')
    tick_postpaid = fields.Boolean('Is Postpaid', default=False)
    url_detail = fields.Char(string='Link for Details')
    ticket_id = fields.Many2one('helpdesk.ticket')

    @api.depends('start_date')
    def compute_start_job(self):
        for rec in self:
            if rec.start_date and not rec.jobsheet_start:
                rec.jobsheet_start = rec.start_date

    @api.onchange('start_date','end_date')
    def onchange_start_end_date(self):
        if self.start_date and self.end_date:
            duration = self.end_date - self.start_date
            print(duration)
            seconds = duration.total_seconds()
            hours = seconds // 3600
            if hours > 8:
                return {
                    'warning': {
                        'title': "Working Hours",
                        'message': "This is just a notification that you are filling more than 8 hours in the Jobsheet.",
                    },
                }

    @api.onchange('tick_postpaid')
    def onchange_tick_postpaid(self):
        if not self.is_prepaid:
            if self.tick_postpaid:
                self.type = 'postpaid'
            else:
                self.type = 'contract'

    @api.depends('partner_id')
    def compute_service_domain(self):
        domain = [('id', 'in', self.partner_id.service_ids.mapped('product_id').ids)] if self.partner_id and self.partner_id.service_ids else [('id', '=', False)]
        self.service_domain = self.env['product.template'].search(domain)

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.timesheet_ids:
            raise UserError(_('You cannot change customer once you filled in a timesheet.'))
        self.service_id = self.partner_id.service_ids[0].product_id.id if self.partner_id.service_ids else False
        if self.partner_id.jobsheet_type == 'prepaid':
            self.is_prepaid = True
            self.type = 'prepaid'
            self.tick_postpaid = False
        else:
            self.is_prepaid = False
            self.tick_postpaid = False
            self.type = 'contract'

    @api.onchange('service_id')
    def onchange_service_id(self):
        if self.timesheet_ids:
            raise UserError(_('You cannot change the service once you filled in a timesheet.'))
        if self.service_id:
            self.project_id = self.service_id.project_id.id
        else:
            self.project_id = False
        if self.type in ['postpaid','contract']:
            self.project_id = self.env.ref('odoo_timestead.project_project_jobsheet').id

    @api.onchange('overtime')
    def onchange_overtime(self):
        if not self.overtime:
            self.hours_overtime = False

    @api.constrains('details')
    def _check_details(self):
        params = self._context.get('params', {})
        if not params:
            for rec in self:
                if rec.details and len(rec.details) <= 50:
                    raise ValidationError(_('Please fill in details with at least 50 characters.'))

    @api.constrains('hours_overtime', 'effective_hours')
    def _check_hours_overtime(self):
        for rec in self:
            if rec.hours_overtime > rec.effective_hours:
                raise ValidationError(_('You cannot go over Hours Spent Time.'))

    @api.depends('timesheet_ids.unit_amount')
    def _compute_effective_hours(self):
        for job in self:
            job.effective_hours = round(sum(job.timesheet_ids.mapped('unit_amount')), 2)

    @api.depends('project_id')
    def compute_task_id(self):
        for job in self:
            tasks = job.project_id.task_ids.filtered(lambda t: t.partner_id == job.partner_id)
            if len(tasks) == 1:
                job.task_id = tasks.id
            elif len(tasks) > 1:
                tasks_filtered = tasks.filtered(lambda t: round(t.progress) < 100)
                if len(tasks_filtered) == 1:
                    job.task_id = tasks_filtered.id
                else:
                    job.task_id = tasks_filtered.filtered(lambda t: t.progress > 0)[0] if tasks_filtered.filtered(lambda t: t.progress > 0) else False
            else:
                job.task_id = False

    def action_timer_stop(self):
        minutes_spent = super(JobSheet, self).action_timer_stop()
        values = {
            'job_id': self.id,
            'project_id': self.project_id.id,
            'task_id': self.task_id.id,
            'date': fields.Datetime.now(),
            'name': self.details or '/',
            'user_id': self.env.uid,
            'unit_amount': minutes_spent / 60,
        }
        self.end_date = fields.Datetime.now()
        timesheet = self.env['account.analytic.line'].create(values)
        self.hours = self.effective_hours
        self.write({
            'timer_start': False,
            'timer_pause': False
        })
        self.timesheet_ids = [(4, timesheet.id, None)]
        self.user_timer_id.unlink()

    def get_email_template_and_send(self, obj):
        template = False
        if obj:
            if obj._name == 'sale.order':
                template = self.env.ref('sale.email_template_edi_sale')
            if obj._name == 'account.move':
                template = self.env.ref('account.email_template_edi_invoice')
            values = self.env['mail.compose.message'].sudo().generate_email_for_composer(
                template.id, [obj.id],
                ['subject', 'body_html', 'email_from', 'email_to', 'partner_to', 'email_cc', 'reply_to',
                 'attachment_ids', 'mail_server_id']
            )[obj.id]
            mail_composer = self.env['mail.compose.message'].with_context(
                default_use_template=bool(template.id),
                mark_so_as_sent=True,
                custom_layout='mail.mail_notification_paynow',
                proforma=self.env.context.get('proforma',
                                              False),
                force_email=True,
                mail_notify_author=True,
                default_model=obj._name,
                default_template_id=template.id,
                default_composition_mode='comment',
                model_description=obj.type_name
            ).sudo().create({
                'res_id': obj.id,
                'subject': values['subject'],
                'body': values['body'],
                'email_from': self.company_id.jobsheet_manager.login if not self.env.user.has_group('odoo_timestead.group_jobsheet_manager') else self.env.user.login,
                'attachment_ids': values['attachments'],
                'partner_ids': [obj.partner_id.id],
                'template_id': template and template.id or False,
                'model': obj._name,
                'composition_mode': 'comment'})
            mail_composer.action_send_mail()

    def create_invoice_from_job(self, buffer):
        service = self.partner_id.service_ids.filtered(
            lambda s: s.product_id == self.task_id.sale_line_id.product_id.product_tmpl_id)[0]
        invoice_id = self.env['account.move'].sudo().create({
            'partner_id': self.partner_id.id,
            'job_ids': [(6, 0, self.ids)],
            'move_type': 'out_invoice',
            'invoice_user_id': self.company_id.jobsheet_manager.id,
            'user_id': self.company_id.jobsheet_manager.id if not self.env.user.has_group('odoo_timestead.group_jobsheet_manager') else self.env.uid,
            'invoice_line_ids': [[0, 0, {
                "name": self.name,
                "quantity": buffer,
                "price_unit": service.hour,
                "product_uom_id": self.env.ref('uom.product_uom_hour').id
            }]]
        })
        invoice_id.sudo().action_post()
        if not self.env.user.has_group('odoo_timestead.group_jobsheet_manager'):
            invoice_id.sudo().message_unsubscribe(partner_ids=[self.env.uid])
        self.get_email_template_and_send(invoice_id)
        message = _(
            "You went over 100%% of your allocated time, a new Invoice : <a href=# data-oe-model=account.move data-oe-id=%d>%s</a> has been created and sent to the customer.") % (
                      invoice_id.id, invoice_id.name)
        self.activity_schedule('mail.mail_activity_delivery_shortfall', note=message,
                               user_id=self.company_id.jobsheet_manager.id if not self.env.user.has_group('odoo_timestead.group_jobsheet_manager') else self.env.uid)
        return invoice_id

    def create_sale_order_from_job(self, res):
        if res:
            self = res
        service = self.partner_id.service_ids.filtered(
            lambda s: s.product_id == self.task_id.sale_line_id.product_id.product_tmpl_id)[0]
        order_id = self.env['sale.order'].sudo().create({
            'partner_id': self.partner_id.id,
            "user_id": self.company_id.jobsheet_manager.id if not self.env.user.has_group('odoo_timestead.group_jobsheet_manager') else self.env.uid,
            'order_line': [[0, 0, {
                "product_id": service.product_id.id,
                "product_uom_qty": service.quantity,
                "price_unit": service.hour,
            }]]
        })
        if not self.env.user.has_group('odoo_timestead.group_jobsheet_manager'):
            order_id.sudo().message_unsubscribe(partner_ids=[self.env.uid])
        self.sudo().sale_order_id = order_id.id
        message = _(
            "You went over 75%% of your allocated time, a new Sales Order : <a href=# data-oe-model=sale.order data-oe-id=%d>%s</a> has been created and sent to the customer.") % (
                      order_id.id, order_id.name)
        self.activity_schedule('mail.mail_activity_delivery_shortfall', note=message,
                               user_id=self.company_id.jobsheet_manager.id if not self.env.user.has_group('odoo_timestead.group_jobsheet_manager') else self.env.uid)
        self.get_email_template_and_send(order_id)


    def trigger_send_quotation(self, last_progress, progress, remaining_hour, current_service):

        if last_progress >=100 :
            raise UserError(_('You cannot go over 100%, please contact your administrator'))
        if progress >= 75 and last_progress < 75:
            #### if we're surpassing 75% #####
            if remaining_hour < 0:
                buffer = current_service.extra_hour
                if abs(remaining_hour) > buffer or buffer <= 0:
                    print(abs(remaining_hour))
                    raise UserError(_('You cannot go over 100%, please contact your administrator'))
                else:
                    current_service.extra_hour = 0
                    self.create_sale_order_from_job(self)
                    self.create_invoice_from_job(abs(remaining_hour))
            else:
                self.create_sale_order_from_job(self)
        ##### Get Sale Order: Look if we already create next Sales to be sent as a remainder ###
        if not self.sudo().sale_order_id:
            sale_obj = self.env['sale.order']
            order_lines = sale_obj.sudo().search([('partner_id', '=',self.partner_id.id),('state','=','sent')]).order_line
            if order_lines:
                sale_order = order_lines.sudo().filtered(lambda s: s.product_id.product_tmpl_id == self.service_id).sudo().order_id[0]
                if sale_order:
                    self.sudo().sale_order_id= sale_order
        ###########"
        if last_progress >= 75:
            if remaining_hour < 0:
                buffer = current_service.extra_hour
                if abs(remaining_hour) > buffer or buffer <= 0:
                    print(abs(remaining_hour))
                    raise UserError(_('You cannot go over 100%, please contact your administrator'))
                else:
                    current_service.extra_hour = 0
                    self.create_invoice_from_job(abs(remaining_hour))
                    self.get_email_template_and_send(self.sale_order_id)
            else:
                self.get_email_template_and_send(self.sale_order_id)

    def create_account_analytic_line(self, values):
        #### This is only in Prepaid mode ###
        if self.type == 'prepaid' and values['unit_amount'] > self.remaining_hours:
            #### if hours surpass progress we have to look if there is a confirmed sales to put in the remaining hours####
            copy_vals = values.copy()
            sale_obj = self.env['sale.order']
            check_next_sale_order = False
            order_lines = sale_obj.sudo().search([('partner_id', '=', self.partner_id.id), ('state', '=', 'sale'),('id','!=',self.task_id.sudo().sale_line_id.sudo().order_id.id)]).sudo().order_line
            if order_lines:
                sale_order = order_lines.sudo().filtered(lambda s: s.product_id.product_tmpl_id == self.service_id and s.qty_delivered ==0).sudo().order_id
                check_next_sale_order = sale_order[0] if sale_order else False
            if check_next_sale_order:
                remaining_hours = values['unit_amount'] - self.remaining_hours
                values['unit_amount'] = self.remaining_hours
                self.env['account.analytic.line'].create(values)
                new_job= self.env['client.jobsheet'].create({
                    'partner_id': self.partner_id.id,
                    'service_id': self.service_id.id,
                    'project_id': self.project_id.id,
                    'type': 'prepaid',
                    'brief': self.brief,
                    'details': self.details,
                    'jobsheet_start': self.start_date,
                    'task_id':check_next_sale_order.tasks_ids[0].id
                })
                copy_vals['job_id'] = new_job.id
                copy_vals['unit_amount'] = remaining_hours
                copy_vals['task_id'] = new_job.task_id.id
                self.env['account.analytic.line'].create(copy_vals)
                message = _(
                    "The current task has been completed with the remaining hours, the rest of the allocated hours are registered in a new jobsheet : <a href=# data-oe-model=client.jobsheet data-oe-id=%d>%s</a>.") % (
                              new_job.id, new_job.name)
                self.activity_schedule('mail.mail_activity_delivery_shortfall', note=message,
                                       user_id=self.user_id.id)

            else:
                self.env['account.analytic.line'].create(values)
        else:
            self.env['account.analytic.line'].create(values)

    @api.model
    def create(self, vals):
        res = super(JobSheet, self).create(vals)
        if vals.get('name', _('New')) == _('New'):
            seq_date = None
            if res.date_order:
                seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(res.date_order))
            res.name = self.env['ir.sequence'].next_by_code('client.jobsheet', sequence_date=seq_date) or _('New')
            if 'partner_id' in vals:
                list_followers = [res.partner_id.id]
                for child in res.partner_id.child_ids:
                    if child.receive_jobsheet:
                        list_followers.append(child.id)
                res.message_subscribe(partner_ids=list_followers)
        if vals.get('ticket_id'):
            ticket = self.env['helpdesk.ticket'].browse(vals['ticket_id'])
            ticket.job_id = res.id
        if vals.get('hours') and vals.get('hours') > 0:
            values = {
                'job_id': res.id,
                'project_id': res.project_id.id,
                'task_id': res.task_id.id,
                'date': fields.Datetime.now(),
                'name': '/',
                'user_id': res.env.uid,
                'unit_amount': vals['hours'],
            }
            if res.partner_id.jobsheet_type =='prepaid' and not res.task_id:
                raise UserError(_('No task found to allocate hours.'))
            last_progress = res.task_id.progress
            current_service = res.partner_id.service_ids.filtered(
                lambda s: s.product_id == res.service_id)[0]
            res.create_account_analytic_line(values)
            if res.type == 'prepaid':
                res.trigger_send_quotation(last_progress, res.task_id.progress, res.remaining_hours, current_service)
        return res

    def write(self, vals):
        if all(key in vals for key in ('start_date', 'end_date')):
            values = {
                'job_id': self.id,
                'project_id': self.project_id.id,
                'task_id': self.task_id.id,
                'date': fields.Datetime.now(),
                'name': '/',
                'user_id': self.env.uid,
                'unit_amount': vals['hours'] if 'hours' in vals else self.hours,
            }
            if self.partner_id.jobsheet_type =='prepaid' and not self.task_id:
                raise UserError(_('No task found to allocate hours.'))
            last_progress = self.task_id.progress
            self.create_account_analytic_line(values)
            if 'hours' in vals:
                vals['hours'] = self.effective_hours
            else:
                self.hours = self.effective_hours
            progress = self.task_id.progress
            current_service = self.partner_id.service_ids.filtered(
                lambda s: s.product_id == self.service_id)[0]
            type = vals.get('type') if vals.get('type') else self.type
            if type == 'prepaid':
                self.trigger_send_quotation(last_progress, progress, self.task_id.remaining_hours, current_service)

        return super(JobSheet, self).write(vals)

    def action_view_project_ids(self):
        self.ensure_one()
        view_form_id = self.env.ref('project.edit_project').id
        view_kanban_id = self.env.ref('project.view_project_kanban').id
        action = {
            'type': 'ir.actions.act_window',
            'domain': [('id', '=', self.project_id.id)],
            'views': [(view_kanban_id, 'kanban'), (view_form_id, 'form')],
            'view_mode': 'kanban,form',
            'name': _('Project'),
            'res_model': 'project.project',
        }
        return action

    def action_view_task_id(self):
        self.ensure_one()
        form_view_id = self.env.ref('project.view_task_form2').id
        action = {
            'type': 'ir.actions.act_window',
            'domain': [('id', '=', self.task_id.id)],
            'views': [(form_view_id, 'form')],
            'view_mode': 'form',
            'res_id': self.task_id.id,
            'name': _('Task'),
            'res_model': 'project.task',
        }
        return action

    @api.depends('timer_start', 'timer_pause')
    def _compute_display_timer_buttons(self):
        for ticket in self:
            ticket.update({
                'display_timer_start_primary': False,
                'display_timer_start_secondary': False,
                'display_timer_stop': False,
                'display_timer_pause': False,
                'display_timer_resume': False,
            })
            super(JobSheet, ticket)._compute_display_timer_buttons()
            ticket.display_timer_start_secondary = ticket.display_timer_start_primary
            if not ticket.timer_start:
                ticket.update({
                    'display_timer_stop': False,
                    'display_timer_pause': False,
                    'display_timer_resume': False,
                })

    @api.depends('jobsheet_line.price_unit')
    def _amount_all(self):
        for order in self:
            amount_total = 0.0
            for line in order.jobsheet_line:
                amount_total += line.price_unit
            order.update({
                'amount_total': amount_total
            })

    def _compute_access_url(self):
        super(JobSheet, self)._compute_access_url()
        for job_id in self:
            job_id.access_url = '/my/jobsheets/%s' % (job_id.id)

    def _get_share_url(self, redirect=False, signup_partner=False, pid=None):

        self.ensure_one()
        if self:
            auth_param = url_encode(self.partner_id.signup_get_auth_param()[self.partner_id.id])
            return self.get_portal_url(query_string='&%s' % auth_param)
        return super(JobSheet, self)._get_share_url(redirect, signup_partner, pid)

    def _get_report_base_filename(self):
        self.ensure_one()
        return '%s' % (self.name)

    @api.depends('move_ids')
    def _get_invoiced(self):

        for order in self:
            invoices = self.env['account.move'].sudo().search(
                [('move_type', 'in', ('out_invoice', 'out_refund'))]).filtered(
                lambda r: r.job_ids and order.id in r.job_ids.ids)
            order.sudo().move_ids = invoices
            order.sudo().move_count = len(invoices)

    def mark_as_signed(self):
        if not self.signature :
            raise UserError(_("Make sure to sign first."))
        if not self.signee :
            raise UserError(_("Please enter the name of the signee."))
        self.status = 'signed'

    def action_jobsheet_confirm(self):
        self.status = 'confirmed'

    def action_jobsheet_send(self):

        self.ensure_one()
        template = self.env.ref('odoo_timestead.email_template_jobsheet', raise_if_not_found=False)
        lang = self.env.context.get('lang')
        if template.lang:
            lang = template._render_lang(self.ids)[self.id]
        ctx = dict(
            default_model="client.jobsheet",
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template.id,
            default_composition_mode='comment',
            force_mail=True,
            mark_job_as_sent=True,
            custom_layout="mail.mail_notification_paynow",
            model_description=self.with_context(lang=lang).name
        )
        return {
            'name': _('Send Jobsheet'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        if self.env.context.get('mark_job_as_sent'):
            self.filtered(lambda o: o.status == 'created').with_context(tracking_disable=True).write({'status': 'sent'})
        return super(JobSheet, self.with_context(mail_post_autofollow=True)).message_post(**kwargs)

    def action_timer_start(self):
        if not self.user_timer_id.timer_start:
            self.start_date = fields.Datetime.now()
            self.end_date = False
            super(JobSheet, self).action_timer_start()

    def action_send_copy(self):

        self.ensure_one()
        template = self.env.ref('odoo_timestead.email_template_jobsheet', raise_if_not_found=False)
        lang = self.env.context.get('lang')
        if template.lang:
            lang = template._render_lang(self.ids)[self.id]
        ctx = dict(
            default_model="client.jobsheet",
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template.id,
            default_composition_mode='comment',
            custom_layout="mail.mail_notification_paynow",
            force_mail=True,
            model_description=self.with_context(lang=lang).name
        )
        return {
            'name': _('Send a Copy'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

    def _prepare_invoice(self, ref):
        invoice_vals = {
            'ref': ref if ref else self.name or '',
            'move_type': 'out_invoice',
            'job_ids': [(6, 0, self.ids)],
            'partner_id': self[0].partner_id.id,
            'invoice_user_id': self.company_id.jobsheet_manager.id,
            'invoice_origin': ref if ref else self.name or '',
            'invoice_line_ids': [],
        }

        return invoice_vals

    def _prepare_account_move_line_from_rate(self):
        self.ensure_one()
        current_service = self.partner_id.service_ids.filtered(
            lambda s: s.product_id == self.service_id)[0]
        res = {
            'name': '%s' % (self.name),
            # 'product_id': product_service.id,
            'product_uom_id': self.env.ref('uom.product_uom_hour').id,
            'quantity': self.effective_hours,
            'price_unit': current_service.hour,
        }
        return res

    def action_create_invoice(self):
        invoice_vals_list = []
        for order in self:
            if (order.status == 'created' and order.company_id.inv_after_sign):
                raise UserError(_("Only signed jobsheets are ready to be invoiced."))
            if order.type != 'postpaid':
                raise UserError(_("You can only invoice Postpaid Type."))
            invoice_vals = order._prepare_invoice(ref=False)
            invoice_vals['invoice_line_ids'].append((0, 0, order.sudo()._prepare_account_move_line_from_rate()))
            for line in order.jobsheet_line:
                invoice_vals['invoice_line_ids'].append((0, 0, line._prepare_account_move_line()))
            invoice_vals_list.append(invoice_vals)
            AccountMove = self.env['account.move'].with_context(default_move_type='out_invoice')
            moves = AccountMove.sudo().create(invoice_vals_list)
            order.sudo().status = 'invoiced'
            return self.action_open_invoice(moves)


    def action_open_invoice(self, invoices):

        return  {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': self.env.ref('account.view_move_form').id,
                'res_model': 'account.move',
                'res_id': invoices.id,
                'target': 'current',
            }

    def action_view_invoice(self):
        invoices = self.mapped('move_ids')
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = invoices.id
        else:
            action = {'type': 'ir.actions.act_window_close'}

        context = {
            'default_type': 'out_invoice',
        }
        if len(self) == 1:
            context.update({
                'default_partner_id': self.partner_id.id,
                'default_invoice_origin': self.mapped('id'),
            })
        action['context'] = context
        return action

    @api.onchange('start_date','end_date')
    def onchange_compute_hours(self):
        for rec in self:
            duration = 0
            if rec.start_date and rec.end_date:
                duration = (rec.end_date - rec.start_date).total_seconds() / 3600
            rec.hours = duration

    def preview_jobsheet(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url': self.get_portal_url(),
        }

class JobSheetline(models.Model):
    _name = "jobsheet.line"
    _description = "Item Details"

    jobsheet_id = fields.Many2one('client.jobsheet')
    name = fields.Text(string='Name', required=True)
    price_unit = fields.Float('Unit Price', required=True, digits='Product Price', default=0.0)
    product_id = fields.Many2one(
        'product.product', string='Product',
        domain="[('sale_ok', '=', True),('type', '=', 'consu')]",
        change_default=True, ondelete='restrict', check_company=True)
    product_uom_qty = fields.Float(string='Quantity', digits='Product Unit of Measure', required=True, default=1.0)

    def _prepare_account_move_line(self):
        self.ensure_one()
        res = {
            'name': '%s: %s' % (self.jobsheet_id.name, self.name),
            'product_id': self.product_id.id,
            'quantity': self.product_uom_qty,
            'price_unit': self.price_unit,
        }
        return res

    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            return
        vals = {}

        vals.update(name=self.product_id.description or self.product_id.name, price_unit=self.product_id.list_price)
        self.update(vals)