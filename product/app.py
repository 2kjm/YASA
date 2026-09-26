"""Acme Invoicing: the demo product YASA supports. Contains one planted bug (see export_invoice)."""
import csv
import io
import os
import subprocess

import sentry_sdk
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response


def _release():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return None


sentry_sdk.init(dsn=os.environ.get("SENTRY_DSN"), release=os.environ.get("RELEASE") or _release(), send_default_pii=True)

INVOICES = {
    "INV-1001": {"customer": "Café Mocha Pvt Ltd", "currency": "INR", "lines": [("Pro plan, Sep", 1, 2499), ("Extra seats", 3, 499)]},
    "INV-1002": {"customer": "Northwind Traders", "currency": "INR", "lines": [("Pro plan, Sep", 1, 2499), ("Extra seats", 2, 499)]},
    "INV-1003": {"customer": "Blue Lotus Studio", "currency": "INR", "lines": [("Pro plan, Sep", 1, 2499)]},
    "INV-1004": {"customer": "Kite and Kettle Co", "currency": "INR", "lines": [("Pro plan, Sep", 1, 2499)]},
}

app = FastAPI(title="Acme Invoicing")


@app.middleware("http")
async def identify_user(request: Request, call_next):
    # The web client sends the signed-in user's email; Sentry events carry it.
    if email := request.headers.get("x-user-email"):
        sentry_sdk.set_user({"email": email})
    return await call_next(request)


def _get(invoice_id):
    if invoice_id not in INVOICES:
        raise HTTPException(404, "invoice not found")
    return INVOICES[invoice_id]


@app.get("/invoices/{invoice_id}")
def get_invoice(invoice_id: str):
    inv = _get(invoice_id)
    total = sum(qty * price for _, qty, price in inv["lines"])
    return {"id": invoice_id, **inv, "total": total}


@app.get("/invoices/{invoice_id}/export")
def export_invoice(invoice_id: str):
    inv = _get(invoice_id)
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["description", "qty", "unit_price", "amount"])
    for desc, qty, price in inv["lines"]:
        w.writerow([desc, qty, price, qty * price])
    # HTTP headers must be ASCII.
    filename = f"{inv['customer']} {invoice_id}.csv".encode("ascii").decode()
    return Response(out.getvalue(), media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="{filename}"'})
