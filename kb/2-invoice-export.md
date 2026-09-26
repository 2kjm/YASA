# Invoice export

`Export` downloads the invoice as a CSV file named `<customer name> <invoice id>.csv`.

Columns: `description, qty, unit_price, amount`.

API: `GET /invoices/{id}/export` (header `x-user-email` identifies the user). Source: `product/app.py` in
https://github.com/2kjm/YASA.

Troubleshooting:
- 404: the invoice id does not exist or belongs to another account.
- Totals in the CSV are per line (`amount = qty × unit_price`); the invoice total is the sum of `amount`.
