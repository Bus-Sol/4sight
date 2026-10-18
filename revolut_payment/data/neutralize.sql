-- disable revolut payment provider
UPDATE payment_provider
   SET revolut_merchant_api_public = NULL,
   revolut_merchant_api_secret = NULL;

