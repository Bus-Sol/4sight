from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)


class ProvetAuthController(http.Controller):

    @http.route('/provet/invoice/create', type='http', auth='public', csrf=False)
    def provet_invoice_webhook(self, **kwargs):

        _logger.info("Provet Invoice Webhook , data=%s",
                     kwargs)

    @http.route('/provet/oauth/callback', type='http', auth='public', csrf=False)
    def oauth_callback(self, **kwargs):
        """Handle OAuth callback from Provet Cloud - Simple HTML response"""
        code = kwargs.get('code')
        state = kwargs.get('state')
        error = kwargs.get('error')
        error_description = kwargs.get('error_description', '')

        _logger.info("OAuth callback received: code=%s, state=%s, error=%s",
                     code, state, error)

        if error:
            return self._simple_html_response(
                "Authorization Failed",
                f"✗ {error_description or error}",
                "danger"
            )

        if not code or not state:
            return self._simple_html_response(
                "Authorization Failed",
                "Missing required parameters: code and state are required",
                "danger"
            )

        # Find the configuration with matching state
        config = request.env['provet.config'].sudo().search([
            ('auth_state', '=', state)
        ], limit=1)

        if not config:
            _logger.error("No configuration found for state: %s", state)
            return self._simple_html_response(
                "Authorization Failed",
                "Invalid state parameter. Please try the authorization process again.",
                "danger"
            )

        try:
            # Handle the callback
            config.handle_oauth_callback(code, state)

            # Success response
            return self._simple_html_response(
                "Authorization Successful",
                "✓ Your Odoo instance is now connected to Provet Cloud.",
                "success"
            )

        except Exception as e:
            _logger.error("Failed to process OAuth callback: %s", str(e))
            return self._simple_html_response(
                "Authorization Failed",
                f"Failed to complete authorization: {str(e)}",
                "danger"
            )

    def _simple_html_response(self, title, message, status_type):
        """Generate a simple HTML response"""
        colors = {
            'success': '#28a745',
            'danger': '#dc3545',
            'warning': '#ffc107',
            'info': '#17a2b8'
        }

        color = colors.get(status_type, '#6c757d')

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{title} - Provet Cloud</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                    background-color: #f8f9fa;
                    margin: 0;
                    padding: 20px;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                }}
                .container {{
                    max-width: 500px;
                    width: 100%;
                }}
                .card {{
                    background: white;
                    border-radius: 10px;
                    box-shadow: 0 5px 20px rgba(0,0,0,0.1);
                    overflow: hidden;
                    text-align: center;
                }}
                .card-header {{
                    background-color: {color};
                    color: white;
                    padding: 25px;
                }}
                .card-body {{
                    padding: 40px;
                }}
                h1 {{
                    margin: 0;
                    font-size: 24px;
                }}
                .message {{
                    font-size: 18px;
                    margin: 25px 0;
                    line-height: 1.5;
                }}
                button {{
                    background-color: {color};
                    color: white;
                    border: none;
                    padding: 12px 30px;
                    font-size: 16px;
                    border-radius: 5px;
                    cursor: pointer;
                    transition: background-color 0.3s;
                }}
                button:hover {{
                    opacity: 0.9;
                }}
                .icon {{
                    font-size: 60px;
                    margin-bottom: 20px;
                }}
                .auto-close {{
                    font-size: 14px;
                    color: #666;
                    margin-top: 15px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="card">
                    <div class="card-header">
                        <h1>{title}</h1>
                    </div>
                    <div class="card-body">
                        <div class="message">{message}</div>
                        <button onclick="window.close(); return false;">
                            Close Window
                        </button>
                        <div class="auto-close">(This window will close automatically in 5 seconds)</div>
                    </div>
                </div>
            </div>
            <script>
                // Auto-close after 5 seconds
                setTimeout(function() {{
                    window.close();
                }}, 5000);

                // Focus the button for better UX
                document.querySelector('button').focus();
            </script>
        </body>
        </html>
        """
        return html