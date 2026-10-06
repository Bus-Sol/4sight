from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
import requests
import logging
import json
from urllib.parse import urlencode, parse_qs, urlparse

_logger = logging.getLogger(__name__)


class ProvetConfig(models.Model):
    _name = 'provet.config'
    _description = 'Provet Cloud Configuration'
    _rec_name = 'instance_name'

    # Basic Configuration
    instance_name = fields.Char('Instance Name', required=True)
    provet_id = fields.Char('Provet ID', required=True, help='Your Provet Cloud instance ID')
    base_url = fields.Char('Base URL', required=True, default='https://provetcloud.com')

    # OAuth2 Credentials
    client_id = fields.Char('Client ID', required=True)
    client_secret = fields.Char('Client Secret', required=True)

    # Grant Type Selection
    grant_type = fields.Selection([
        ('authorization_code', 'Authorization Code'),
        ('client_credentials', 'Client Credentials'),
    ], string='Grant Type', default='authorization_code', required=True)

    # For Authorization Code Flow
    username = fields.Char('Username')
    password = fields.Char('Password')
    redirect_uri = fields.Char('Redirect URI',
                               default=lambda self: self._get_default_redirect_uri(),
                               help='Must match the redirect URI configured in Provet Cloud')

    # Authorization Code Flow State
    auth_code = fields.Char('Authorization Code', readonly=True)
    auth_state = fields.Char('Authorization State', readonly=True)
    auth_url = fields.Char('Authorization URL', compute='_compute_auth_url')

    # Token Storage
    access_token = fields.Char('Access Token')
    refresh_token = fields.Char('Refresh Token')
    token_expiry = fields.Datetime('Token Expiry')

    # Status Fields
    is_active = fields.Boolean('Active', default=True)
    last_sync = fields.Datetime('Last Sync')
    connection_status = fields.Selection([
        ('not_configured', 'Not Configured'),
        ('auth_required', 'Authorization Required'),
        ('connected', 'Connected'),
        ('expired', 'Token Expired'),
        ('error', 'Error'),
    ], string='Connection Status', default='not_configured', compute='_compute_connection_status', store=True)

    # API Endpoints (computed)
    authorize_url = fields.Char('Authorize URL', compute='_compute_endpoints')
    token_url = fields.Char('Token URL', compute='_compute_endpoints')
    revoke_url = fields.Char('Revoke URL', compute='_compute_endpoints')

    def _get_default_redirect_uri(self):
        """Generate default redirect URI based on current Odoo instance"""
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return f"{base_url}/provet/oauth/callback"

    @api.depends('base_url', 'provet_id')
    def _compute_endpoints(self):
        for config in self:
            if config.base_url and config.provet_id:
                base = config.base_url.rstrip('/')
                provet_id = config.provet_id.strip('/')
                config.authorize_url = f"{base}/{provet_id}/oauth2/authorize/"
                config.token_url = f"{base}/{provet_id}/oauth2/token/"
                config.revoke_url = f"{base}/{provet_id}/oauth2/revoke_token/"
            else:
                config.authorize_url = False
                config.token_url = False
                config.revoke_url = False

    @api.depends('authorize_url', 'client_id', 'redirect_uri', 'auth_state')
    def _compute_auth_url(self):
        """Generate the full authorization URL with parameters"""
        for config in self:
            if not config.authorize_url or not config.client_id:
                config.auth_url = False
                continue

            # Generate a unique state parameter to prevent CSRF
            if not config.auth_state:
                import secrets
                config.write({'auth_state': secrets.token_urlsafe(16)})

            params = {
                'response_type': 'code',
                'client_id': config.client_id,
                'scope': 'restapi openid',
                'redirect_uri': config.redirect_uri,
                'state': config.auth_state,
            }

            config.auth_url = f"{config.authorize_url}?{urlencode(params)}"

    @api.depends('access_token', 'token_expiry', 'grant_type', 'auth_code')
    def _compute_connection_status(self):
        for config in self:
            if config.grant_type == 'authorization_code':
                if not config.auth_code and not config.access_token:
                    config.connection_status = 'auth_required'
                elif config.access_token and config.token_expiry and datetime.now() > config.token_expiry:
                    config.connection_status = 'expired'
                elif config.access_token:
                    config.connection_status = 'connected'
                else:
                    config.connection_status = 'not_configured'
            else:
                if not config.access_token:
                    config.connection_status = 'not_configured'
                elif config.token_expiry and datetime.now() > config.token_expiry:
                    config.connection_status = 'expired'
                else:
                    config.connection_status = 'connected'

    # Main Methods
    def get_access_token(self):
        """Get access token using the configured grant type"""
        self.ensure_one()

        if self.grant_type == 'client_credentials':
            return self._get_client_credentials_token()
        elif self.grant_type == 'authorization_code':
            if not self.auth_code:
                # Return authorization URL for user to visit
                return {
                    'type': 'ir.actions.act_url',
                    'url': self.auth_url,
                    'target': 'new',
                }
            return self._exchange_code_for_token()
        else:
            raise ValidationError(_("Unsupported grant type"))

    def generate_auth_url(self):
        """Generate and return the authorization URL"""
        self.ensure_one()

        if self.grant_type != 'authorization_code':
            raise ValidationError(_("Authorization URL is only available for Authorization Code flow"))

        return {
            'type': 'ir.actions.act_url',
            'url': self.auth_url,
            'target': 'new',
        }

    def _get_client_credentials_token(self):
        """Get token using Client Credentials flow"""
        try:
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
            }

            data = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
            }

            response = requests.post(self.token_url, headers=headers, data=data, timeout=30)
            response.raise_for_status()

            token_data = response.json()
            return self._store_token_data(token_data)

        except requests.exceptions.RequestException as e:
            _logger.error("Failed to get client credentials token: %s", str(e))
            raise ValidationError(_("Failed to connect to Provet Cloud: %s") % str(e))

    def handle_oauth_callback(self, code, state):
        """Handle the OAuth callback with authorization code"""
        self.ensure_one()

        # Verify state parameter matches
        if state != self.auth_state:
            _logger.error("State mismatch: expected %s, got %s", self.auth_state, state)
            raise ValidationError(_("Invalid state parameter. Possible CSRF attack."))

        # Store the authorization code
        self.write({'auth_code': code})

        # Exchange code for tokens
        return self._exchange_code_for_token()

    def _exchange_code_for_token(self):
        """Exchange authorization code for access token"""
        if not self.auth_code:
            raise ValidationError(_("No authorization code available"))

        try:
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
            }

            data = {
                'grant_type': 'authorization_code',
                'code': self.auth_code,
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'redirect_uri': self.redirect_uri,
            }

            response = requests.post(self.token_url, headers=headers, data=data, timeout=30)
            response.raise_for_status()

            token_data = response.json()

            # Clear the auth code after successful exchange
            self.write({'auth_code': False})

            return self._store_token_data(token_data)

        except requests.exceptions.RequestException as e:
            _logger.error("Failed to exchange code for token: %s", str(e))
            raise ValidationError(_("Failed to get access token: %s") % str(e))

    def refresh_access_token(self):
        """Refresh expired access token using refresh token"""
        self.ensure_one()

        if not self.refresh_token:
            if self.grant_type == 'authorization_code':
                # Need to re-authorize
                self.write({'access_token': False, 'auth_code': False})
                return self.generate_auth_url()
            raise ValidationError(_("No refresh token available. Please re-authenticate."))

        try:
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
            }

            data = {
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token,
                'client_id': self.client_id,
                'client_secret': self.client_secret,
            }

            response = requests.post(self.token_url, headers=headers, data=data, timeout=30)
            response.raise_for_status()

            token_data = response.json()
            return self._store_token_data(token_data)

        except requests.exceptions.RequestException as e:
            _logger.error("Failed to refresh token: %s", str(e))
            # If refresh token is invalid, clear it and require re-auth
            if response.status_code == 400:
                self.write({'refresh_token': False, 'access_token': False})
                raise ValidationError(_("Refresh token invalid. Please re-authenticate."))
            raise ValidationError(_("Failed to refresh token: %s") % str(e))

    def _store_token_data(self, token_data):
        """Store token data in the model"""
        self.ensure_one()

        self.access_token = token_data.get('access_token')
        self.refresh_token = token_data.get('refresh_token', self.refresh_token)

        # Calculate expiry (Provet tokens expire in 10 hours)
        expires_in = token_data.get('expires_in', 36000)  # Default 10 hours
        expiry_time = datetime.now() + timedelta(seconds=expires_in)
        self.token_expiry = expiry_time

        self.last_sync = datetime.now()

        _logger.info("Token stored successfully for %s", self.instance_name)
        return True

    def test_connection(self):
        """Test the connection to Provet Cloud"""
        self.ensure_one()

        try:
            # Get or refresh token
            if not self.access_token or (self.token_expiry and datetime.now() > self.token_expiry):
                if self.refresh_token:
                    self.refresh_access_token()
                else:
                    result = self.get_access_token()
                    if isinstance(result, dict) and result.get('type') == 'ir.actions.act_url':
                        # Need user authorization first
                        return {
                            'type': 'ir.actions.client',
                            'tag': 'display_notification',
                            'params': {
                                'title': 'Authorization Required',
                                'message': 'Please authorize the application first by visiting the authorization URL',
                                'type': 'warning',
                                'sticky': True,
                            }
                        }

            # Make a test API call
            test_url = f"{self.base_url}/{self.provet_id}/api/v1/"  # Adjust based on Provet API
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json',
            }

            response = requests.get(test_url, headers=headers, timeout=30)
            response.raise_for_status()

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Success',
                    'message': 'Connection test successful!',
                    'type': 'success',
                    'sticky': False,
                }
            }

        except Exception as e:
            _logger.error("Connection test failed: %s", str(e))
            raise ValidationError(_("Connection test failed: %s") % str(e))

    def check_auth_status(self):
        """Check and return authorization status"""
        self.ensure_one()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Authorization Status',
                'message': f'Status: {self.connection_status}. Token expires: {self.token_expiry or "Never"}',
                'type': 'info' if self.connection_status == 'connected' else 'warning',
                'sticky': True,
            }
        }