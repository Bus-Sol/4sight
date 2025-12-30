from odoo import api, fields, models,_lt
from odoo.http import request
import logging
_logger = logging.getLogger(__name__)


class Website(models.Model):
    _inherit = 'website'

    def _get_checkout_steps(self, current_step=None):
        """ Override of `website_sale` to add an "Invoicing info" step when needed.

        If `current_step` is provided, returns only the corresponding step.

        Note: self.ensure_one()

        :param str current_step: The xmlid of the current step, defaults to None.
        :rtype: list
        :return: A list with the following structure:
            [
                [xmlid],
                {
                    'name': str,
                    'current_href': str,
                    'main_button': str,
                    'main_button_href': str,
                    'back_button': str,
                    'back_button_href': str
                }
            ]
        """
        checkout_steps = super()._get_checkout_steps(current_step=None)
        order = self.sale_get_order()
        _logger.info("order to check %s", order)
        _logger.info("order to check.sale_order_template_id %s", order.sale_order_template_id)
        flow_temp = self.env['sale.order.template'].sudo().search([('is_flow_template' ,'=', True)], limit=1)

        flow = order.sale_order_template_id == flow_temp.id
        custom_kwargs = request.session.get('custom_checkout_data', {})
        categ_id = False

        if custom_kwargs:
            # Now you can use your passed values
            categ_id = custom_kwargs.get('event_categ_id')

        if flow or categ_id:
            _logger.info("order to check is flow")
            previous_step = next(
                step for step in checkout_steps if 'website_sale.payment' in step[0]
            )
            _logger.info("previous_step ???  %s", previous_step)
            previous_step_index = checkout_steps.index(previous_step)


            checkout_steps[previous_step_index][1]['back_button'] = _lt("Return")
            checkout_steps[previous_step_index][1]['back_button_href'] = '/shop/clear_and_back'

        if current_step:
            return next(
                step for step in checkout_steps if current_step in step[0]
            )[1]
        else:
            return checkout_steps