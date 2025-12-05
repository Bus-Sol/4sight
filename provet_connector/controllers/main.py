from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)


class ProvetAuthController(http.Controller):

    @http.route('/provet/oauth/callback', type='http', auth='public', website=True, csrf=False)
    def oauth_callback(self, **kwargs):
        """Handle OAuth callback from Provet Cloud"""
        code = kwargs.get('code')
        state = kwargs.get('state')
        error = kwargs.get('error')
        error_description = kwargs.get('error_description', '')

        _logger.info("OAuth callback received: code=%s, state=%s, error=%s",
                     code, state, error)

        if error:
            return request.render('provet_connector.oauth_error', {
                'error_message': f"Authorization failed: {error_description or error}"
            })

        if not code or not state:
            return request.render('provet_connector.oauth_error', {
                'error_message': "Missing required parameters: code and state are required"
            })

        # Find the configuration with matching state
        config = request.env['provet.config'].sudo().search([
            ('auth_state', '=', state)
        ], limit=1)

        if not config:
            _logger.error("No configuration found for state: %s", state)
            return request.render('provet_connector.oauth_error', {
                'error_message': "Invalid state parameter. Please try the authorization process again."
            })

        try:
            # Handle the callback
            config.handle_oauth_callback(code, state)

            # Render success page
            return request.render('provet_connector.oauth_success', {})

        except Exception as e:
            _logger.error("Failed to process OAuth callback: %s", str(e))
            return request.render('provet_connector.oauth_error', {
                'error_message': f"Failed to complete authorization: {str(e)}"
            })

    @http.route('/provet/oauth/check-status/<int:config_id>', type='json', auth='user')
    def check_auth_status(self, config_id, **kwargs):
        """Check OAuth status for a configuration (JSON endpoint)"""
        config = request.env['provet.config'].browse(config_id)
        if not config.exists():
            return {
                'success': False,
                'error': 'Configuration not found'
            }

        return {
            'success': True,
            'status': config.connection_status,
            'has_token': bool(config.access_token),
            'token_expiry': config.token_expiry.strftime('%Y-%m-%d %H:%M:%S') if config.token_expiry else None,
        }