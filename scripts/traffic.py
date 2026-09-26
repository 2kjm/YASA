"""Use the running product as each demo customer, so real Sentry events exist (Café Mocha's export fails).
Start the app first (see README), then: uv run --env-file .env scripts/traffic.py"""
import urllib.error
import urllib.request

from seed_stripe import CUSTOMERS, email

BASE = "http://localhost:8765"

for tag, name, invoice in CUSTOMERS:
    for path in (f"/invoices/{invoice}", f"/invoices/{invoice}/export"):
        req = urllib.request.Request(BASE + path, headers={"x-user-email": email(tag)})
        try:
            status = urllib.request.urlopen(req).status
        except urllib.error.HTTPError as e:
            status = e.code
        print(f"{status}  {email(tag):40} {path}")
