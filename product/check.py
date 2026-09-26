"""Self-check: the planted bug fires for Café Mocha only. Run: uv run --with-requirements product/requirements.txt python product/check.py"""
from fastapi.testclient import TestClient

from app import app

c = TestClient(app, raise_server_exceptions=False)
assert c.get("/invoices/INV-1002/export").status_code == 200
assert c.get("/invoices/INV-1001").json()["total"] == 2499 + 3 * 499
assert c.get("/invoices/INV-1001/export").status_code == 500, "planted bug missing"
assert c.get("/invoices/INV-9999").status_code == 404
print("ok")
