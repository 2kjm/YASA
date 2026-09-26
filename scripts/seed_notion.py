"""Create the Notion CRM (database "Customers") and the "Knowledge base" pages through TrueForge's Notion connector.
Needs TrueForge running and the notion connector authorized. Run once: uv run --env-file .env scripts/seed_notion.py"""
import json
import os
import pathlib
import time

from customers import CUSTOMERS, email
from register import ROOT, call

rows = [{"Company": c, "Email": email(tag), "Contact": contact, "Plan": "Pro", "Status": "Active", "Customer since": since}
        for tag, c, contact, since, _ in CUSTOMERS]
kb = []
for f in sorted((ROOT / "kb").glob("*.md")):
    title, _, body = f.read_text().partition("\n")
    kb.append({"title": title.lstrip("# ").strip(), "content": body.strip()})

task = f"""Set up this Notion workspace for the Acme Invoicing support demo. Copy all text exactly as given.

1. Call notion-get-tool-access. Then search for an existing database "Customers" and page "Knowledge base".
   If either already exists, create nothing and report what exists.
2. Create a workspace-level database titled "Customers" with this schema:
   CREATE TABLE ("Company" TITLE, "Email" EMAIL, "Contact" RICH_TEXT, "Plan" SELECT('Pro':blue, 'Free':gray), "Status" SELECT('Active':green, 'Cancelled':red), "Customer since" DATE)
3. Create these rows in that database's data source (one page per row):
{json.dumps(rows, ensure_ascii=False, indent=1)}
4. Create a workspace-level page titled "Knowledge base" with content "Support knowledge base for Acme Invoicing."
5. Under "Knowledge base", create one child page per item below: title from "title", body exactly from "content":
{json.dumps(kb, ensure_ascii=False, indent=1)}
6. Reply with: the Customers database URL and data source id, the Knowledge base page URL, and the 5 child page URLs."""

spec = {
    "model": {"name": os.environ["GUIDE_MODEL"], "params": {"reasoning_effort": "medium"}},
    "instructions": "You set up Notion content exactly as instructed. Creating pages and databases is expected here.",
    "mcp_servers": [{"name": "notion", "require_approval_for_tools": [], "enable_tools": [
        "notion-get-tool-access", "notion-search", "notion-fetch", "notion-create-database", "notion-create-pages"]}],
    "config": {"iteration_limit": 60},
}
sid = call("POST", "/sessions", {"agent": {"spec": spec}})["data"]["id"]
turn = call("POST", f"/sessions/{sid}/turns", {"input": [{"type": "user.message", "content": task}], "stream": False})["data"]
print(f"seeding Notion in TrueForge session {sid} ...", flush=True)
while turn["state"]["status"] == "running":
    time.sleep(10)
    turn = call("GET", f"/sessions/{sid}/turns/{turn['id']}")["data"]
events = call("GET", f"/sessions/{sid}/turns/{turn['id']}/events")["data"]
last = [e["content"] for e in events if e["type"] == "model.message" and e.get("content")]
print(turn["state"]["status"], "\n", last[-1] if last else "(no final message)")
