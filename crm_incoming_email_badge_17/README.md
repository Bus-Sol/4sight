# CRM Incoming Email Badge — Odoo 17 v3

Replace the existing `crm_incoming_email_badge_17` module folder with this
version. Keep the technical folder name exactly:

`crm_incoming_email_badge_17`

## Status behavior

- Red badge: one or more external customer emails are waiting.
- Green badge: an internal Odoo user posted a public reply after the latest
  customer email.
- Internal notes do not change the status.
- A new customer reply changes green back to red.

## Not included

- CRM Inbox menu
- Browser notifications
- Waiting-time dashboard

## Upgrade

```bash
./odoo-bin -c /etc/odoo/odoo.conf -d YOUR_DATABASE \
    -u crm_incoming_email_badge_17 --stop-after-init
```

After upgrading, restart Odoo and hard-refresh the browser.
