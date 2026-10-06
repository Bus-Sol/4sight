import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Rebuild global CRM communication status after installation/upgrade."""
    leads = env["crm.lead"].sudo().search([])
    if leads:
        _logger.info("CRM Sales Guard: recalculating %s CRM records", len(leads))
        leads._recompute_sales_communication_status()
