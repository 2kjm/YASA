"""Create the demo customers on a "Pro" subscription in Stripe TEST mode. Safe to re-run.
Run: uv run --env-file .env scripts/seed_stripe.py"""
import base64
import json
import os
import urllib.parse
import urllib.request

# (plus-address tag, company, their invoice in product/app.py). The spam sender (+spam) is deliberately absent.
CUSTOMERS = [
    ("cafemocha", "Café Mocha Pvt Ltd", "INV-1001"),
    ("totals", "Northwind Traders", "INV-1002"),
    ("attach", "Blue Lotus Studio", "INV-1003"),
    ("known", "Kite and Kettle Co", "INV-1004"),
]


def email(tag):
    user, domain = os.environ["DEMO_EMAIL_BASE"].split("@")
    return f"{user}+{tag}@{domain}"


def stripe(method, path, **params):
    key = os.environ["STRIPE_SECRET_KEY"]
    if not key.startswith("sk_test_"):
        raise SystemExit("STRIPE_SECRET_KEY must be a test-mode key (sk_test_...)")
    data = urllib.parse.urlencode(params).encode()
    url = f"https://api.stripe.com/v1/{path}"
    if method == "GET":
        url, data = f"{url}?{data.decode()}", None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", "Basic " + base64.b64encode(f"{key}:".encode()).decode())
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def main():
    prices = stripe("GET", "prices", **{"lookup_keys[]": "acme_pro_monthly"})["data"]
    price = prices[0] if prices else stripe(
        "POST", "prices", currency="usd", unit_amount=2900, lookup_key="acme_pro_monthly",
        **{"recurring[interval]": "month", "product_data[name]": "Acme Invoicing Pro"})
    for tag, name, _ in CUSTOMERS:
        found = stripe("GET", "customers", email=email(tag))["data"]
        cust = found[0] if found else stripe("POST", "customers", email=email(tag), name=name)
        if not stripe("GET", "subscriptions", customer=cust["id"])["data"]:
            # send_invoice: active without a card, so no payment-method setup in test mode.
            stripe("POST", "subscriptions", customer=cust["id"], collection_method="send_invoice",
                   days_until_due=30, **{"items[0][price]": price["id"]})
        print(f"{email(tag):40} {name:22} {cust['id']}")


if __name__ == "__main__":
    main()
