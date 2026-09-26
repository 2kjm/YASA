"""Demo customers, shared by seed_notion.py (the Notion CRM rows) and traffic.py (the Sentry events)."""
import os

# (plus-address tag, company, contact, customer since, their invoice in product/app.py).
# The spam sender (+spam) is deliberately absent.
CUSTOMERS = [
    ("cafemocha", "Café Mocha Pvt Ltd", "Priya Nair", "2026-03-02", "INV-1001"),
    ("totals", "Northwind Traders", "Arjun Mehta", "2026-05-14", "INV-1002"),
    ("attach", "Blue Lotus Studio", "Meera Iyer", "2026-06-20", "INV-1003"),
    ("known", "Kite and Kettle Co", "Rohan Das", "2026-01-11", "INV-1004"),
]


def email(tag):
    user, domain = os.environ["DEMO_EMAIL_BASE"].split("@")
    return f"{user}+{tag}@{domain}"

