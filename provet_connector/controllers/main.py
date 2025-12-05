from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)


class ProvetAuthController(http.Controller):

    @http.route('/provet/oauth/callback', type='http', auth='public', website=True)
    def oauth_callback(self, **kwargs):
        """Handle OAuth callback from Provet Cloud"""
        code = kwargs.get('code')
        state = kwargs.get('state')
        error = kwargs.get('error')

        _logger.info("OAuth callback received: code=%s, state=%s, error=%s",
                     code, state, error)

        if error:
            return self._render_error_page(f"Authorization failed: {error}")

        if not code or not state:
            return self._render_error_page("Missing required parameters")

        # Find the configuration with matching state
        config = request.env['provet.config'].sudo().search([
            ('auth_state', '=', state)
        ], limit=1)

        if not config:
            _logger.error("No configuration found for state: %s", state)
            return self._render_error_page("Invalid state parameter")

        try:
            # Handle the callback
            config.handle_oauth_callback(code, state)

            # Render success page
            return request.render('provet_connector.oauth_success', {
                'config': config,
            })

        except Exception as e:
            _logger.error("Failed to process OAuth callback: %s", str(e))
            return self._render_error_page(str(e))

    def _render_error_page(self, error_message):
        """Render error page"""
        return request.render('provet_connector.oauth_error', {
            'error_message': error_message,
        })

    @http.route('/provet/oauth/status/<int:config_id>', type='http', auth='user', website=True)
    def oauth_status(self, config_id, **kwargs):
        """Check OAuth status for a configuration"""
        config = request.env['provet.config'].browse(config_id)
        if not config.exists():
            return request.render('provet_connector.oauth_error', {
                'error_message': 'Configuration not found',
            })

        return request.render('provet_connector.oauth_status', {
            'config': config,
        })