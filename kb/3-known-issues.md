# Known issues

## Invoice emails land in Outlook / Hotmail Junk folder

- **Status**: open, fix planned (DKIM alignment for `billing@acme-invoicing.example`).
- **Symptom**: clients using Outlook.com or Microsoft 365 find Acme invoice emails in Junk.
- **Workaround**: ask the client to add `billing@acme-invoicing.example` to Safe senders, or send the invoice
  link directly from the invoice page (`Copy link`).
- **Reply to customers**: confirm it is known, give the workaround, no date promises.
