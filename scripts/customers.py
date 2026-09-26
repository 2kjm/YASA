"""Demo customers. Run it to write customers.csv, then import that into Notion as the "Customers" database (the CRM).
Run: uv run --env-file .env scripts/customers.py"""
import csv
import os
import pathlib

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


if __name__ == "__main__":
    out = pathlib.Path(__file__).resolve().parent.parent / "customers.csv"
    with out.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Company", "Email", "Contact", "Plan", "Status", "Customer since"])
        for tag, company, contact, since, _ in CUSTOMERS:
            w.writerow([company, email(tag), contact, "Pro", "Active", since])
    print(f"wrote {out}: import it into Notion as a database named Customers")
