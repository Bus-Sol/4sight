from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
import requests
import logging
import json

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
    ], string='Grant Type', default='client_credentials', required=True)

    # For Authorization Code Flow
    username = fields.Char('Username')
    password = fields.Char('Password')
    redirect_uri = fields.Char('Redirect URI', default='http://localhost:8069/provet/callback')

    # Token Storage
    access_token = fields.Char('Access Token')
    refresh_token = fields.Char('Refresh Token')
    token_expiry = fields.Datetime('Token Expiry')

    # Status Fields
    is_active = fields.Boolean('Active', default=True)
    last_sync = fields.Datetime('Last Sync')
    connection_status = fields.Selection([
        ('not_configured', 'Not Configured'),
        ('connected', 'Connected'),
        ('expired', 'Token Expired'),
        ('error', 'Error'),
    ], string='Connection Status', default='not_configured', compute='_compute_connection_status', store=True)

    # API Endpoints (computed)
    authorize_url = fields.Char('Authorize URL', compute='_compute_endpoints')
    token_url = fields.Char('Token URL', compute='_compute_endpoints')
    revoke_url = fields.Char('Revoke URL', compute='_compute_endpoints')

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

    @api.depends('access_token', 'token_expiry')
    def _compute_connection_status(self):
        for config in self:
            if not config.access_token:
                config.connection_status = 'not_configured'
            elif config.token_expiry and datetime.now() > config.token_expiry:
                config.connection_status = 'expired'
            else:
                config.connection_status = 'connected'

    # Validation
    @api.constrains('grant_type', 'username', 'password')
    def _check_credentials(self):
        for config in self:
            if config.grant_type == 'authorization_code' and (not config.username or not config.password):
                raise ValidationError(_("Username and password are required for Authorization Code flow"))

    # Main Methods
    def get_access_token(self):
        """Get access token using the configured grant type"""
        self.ensure_one()

        if self.grant_type == 'client_credentials':
            return self._get_client_credentials_token()
        elif self.grant_type == 'authorization_code':
            return self._get_authorization_code_token()
        else:
            raise ValidationError(_("Unsupported grant type"))

    def _get_client_credentials_token(self):
        """Get token using Client Credentials flow[citation:3]"""
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

    def _get_authorization_code_token(self):
        """Get token using Authorization Code flow[citation:3]"""
        try:
            # Step 1: Get authorization code
            auth_params = {
                'response_type': 'code',
                'client_id': self.client_id,
                'scope': 'restapi openid',
                'redirect_uri': self.redirect_uri,
            }

            # Note: This would typically redirect to Provet login page
            # For automation, you might need to handle the login via API
            # if Provet supports programmatic login

            # This is a simplified version - in production you'd need
            # to handle the full OAuth2 flow with user interaction

            raise ValidationError(
                _("Authorization Code flow requires user interaction. Please use Client Credentials for background processes."))

        except Exception as e:
            _logger.error("Authorization code flow error: %s", str(e))
            raise

    def refresh_access_token(self):
        """Refresh expired access token using refresh token[citation:3]"""
        self.ensure_one()

        if not self.refresh_token:
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
            raise ValidationError(_("Failed to refresh token: %s") % str(e))

    def _store_token_data(self, token_data):
        """Store token data in the model"""
        self.ensure_one()

        self.access_token = token_data.get('access_token')
        self.refresh_token = token_data.get('refresh_token', self.refresh_token)

        # Calculate expiry (Provet tokens expire in 10 hours)[citation:3]
        expires_in = token_data.get('expires_in', 36000)  # Default 10 hours
        expiry_time = datetime.now() + timedelta(seconds=expires_in)
        self.token_expiry = expiry_time

        self.last_sync = datetime.now()

        _logger.info("Token stored successfully for %s", self.instance_name)
        return True

    def revoke_token(self):
        """Revoke current token[citation:3]"""
        self.ensure_one()

        if not self.access_token:
            raise ValidationError(_("No active token to revoke"))

        try:
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
            }

            data = {
                'token': self.access_token,
                'token_type_hint': 'access_token',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
            }

            response = requests.post(self.revoke_url, headers=headers, data=data, timeout=30)
            response.raise_for_status()

            # Clear stored tokens
            self.access_token = False
            self.refresh_token = False
            self.token_expiry = False

            _logger.info("Token revoked successfully for %s", self.instance_name)
            return True

        except requests.exceptions.RequestException as e:
            _logger.error("Failed to revoke token: %s", str(e))
            raise ValidationError(_("Failed to revoke token: %s") % str(e))

    def test_connection(self):
        """Test the connection to Provet Cloud"""
        self.ensure_one()

        try:
            # Get or refresh token
            if not self.access_token or (self.token_expiry and datetime.now() > self.token_expiry):
                if self.refresh_token:
                    self.refresh_access_token()
                else:
                    self.get_access_token()

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

    def call_provet_api(self, endpoint, method='GET', data=None, params=None):
        """Generic method to call Provet API"""
        self.ensure_one()

        # Ensure we have a valid token
        if not self.access_token or (self.token_expiry and datetime.now() > self.token_expiry):
            if self.refresh_token:
                self.refresh_access_token()
            else:
                self.get_access_token()

        # Build URL and headers
        url = f"{self.base_url}/{self.provet_id}/api/v1/{endpoint.lstrip('/')}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
        }

        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=30)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=headers, json=data, timeout=30)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                raise ValidationError(_("Unsupported HTTP method"))

            response.raise_for_status()
            return response.json() if response.content else True

        except requests.exceptions.RequestException as e:
            _logger.error("API call failed: %s", str(e))
            raise ValidationError(_("API call failed: %s") % str(e))