# CRM Sales Communication Guard — Odoo 17

Commercial-ready CRM communication control for Odoo 17.

## Main capabilities

- Customer email waiting/replied status.
- Internal notes tracked separately.
- Per-user unread customer and internal-note counters.
- Real-time Odoo toast notifications.
- Optional native browser notifications after the user clicks the bell icon and grants permission.
- Sales activity warnings: overdue and no next action.
- Sales Attention manager view and filters.
- Logic-free OWL kanban conditions.
- Recalculation after message creation, edit, deletion, import, and module installation.

## Upgrade from an earlier version

Keep the technical folder name exactly:

`crm_incoming_email_badge_17`

Replace the old folder contents in Git, push, and upgrade the module:

```bash
odoo-bin -d YOUR_DATABASE -u crm_incoming_email_badge_17 --stop-after-init
```

Then restart the Odoo.sh build if needed and hard-refresh the browser.

## Browser notification behavior

Odoo toast notifications work while the web client is connected.
Native browser notifications require the user to click the bell icon in the top bar and grant browser permission. They are delivered while the Odoo browser session is active; this module does not include an external service-worker push gateway.

## Scope

This addon follows the CRM sales process only. It intentionally does not implement SLA or Helpdesk behavior.


## Internal note visibility

- The grey **Notes** badge is global and remains visible to all CRM users when internal notes exist.
- The blue **New Note** badge is per user and appears only for users who received an unread internal-note event.
- The note author is excluded from their own unread notification, but still sees the global Notes badge.


17.0.6.1.0
------------
- Hardened internal-note recognition for standard and custom internal subtypes.
- Added a CRM ``message_post`` safety hook so chatter notes cannot be missed.
