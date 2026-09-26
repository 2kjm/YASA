"""Create or update the custom Freshdesk MCP server, both agents and the two 30-minute schedules. Safe to re-run.
Run: uv run --env-file .env scripts/register.py        (register)
     uv run --env-file .env scripts/register.py run    (also trigger a triage sweep now)"""
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
API = os.environ.get("TRUEFORGE_URL", "http://localhost:8790") + "/api/v1"
# TrueForge allows one trigger per hour per schedule, so two offset schedules give a 30-minute sweep.
SCHEDULES = {"triage-on-the-hour": "0 * * * *", "triage-half-past": "30 * * * *"}


def call(method, path, body=None):
    req = urllib.request.Request(API + path, method=method, data=json.dumps(body).encode() if body else None,
                                 headers={"content-type": "application/json"})
    try:
        with urllib.request.urlopen(req) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise SystemExit(f"{method} {path} -> {e.code}: {e.read().decode()}")


def resolve(value):
    # "$VAR" -> env var, "@path" -> file contents (relative to repo root, "${VAR}" inside filled from env) when that
    # file exists, so tool selectors like "@read-only" pass through
    if isinstance(value, dict):
        return {k: resolve(v) for k, v in value.items()}
    if isinstance(value, list):
        return [resolve(v) for v in value]
    if isinstance(value, str) and value.startswith("$"):
        return os.environ[value[1:]]
    if isinstance(value, str) and value.startswith("@") and (ROOT / value[1:]).is_file():
        return re.sub(r"\$\{(\w+)\}", lambda m: os.environ[m[1]], (ROOT / value[1:]).read_text())
    return value


def upsert_mcp_servers():
    # Catalog connectors (sentry, notion) use OAuth and are connected in the TrueForge UI.
    servers = [
        {"type": "remote", "name": "freshdesk", "url": f"https://{os.environ['FRESHDESK_DOMAIN']}/mcp",
         "description": "Freshdesk support desk: tickets, requesters, replies, tags.",
         "auth": {"type": "header", "headers": {"Authorization": os.environ["FRESHDESK_API_KEY"].strip()}}},
    ]
    for manifest in servers:
        call("PUT", "/settings/mcp-servers", {"manifest": manifest})
        print("mcp server", manifest["name"], "saved")


def upsert_agent(spec):
    existing = [a for a in call("GET", f"/agents?agent_name={spec['name']}")["data"] if a["name"] == spec["name"]]
    if existing:
        call("PUT", f"/agents/{existing[0]['id']}", {"description": spec["description"], "manifest": spec["manifest"]})
    else:
        call("POST", "/agents", spec)
    print("agent", spec["name"], "updated" if existing else "created")


def upsert_schedules():
    existing = {s["name"]: s for s in call("GET", "/schedules?agent_names=support-triage")["data"]}
    for name, cron in SCHEDULES.items():
        manifest = {"task": "Run the triage sweep now.", "cron": cron, "timezone": "Asia/Kolkata", "status": "active"}
        if name in existing:
            call("PUT", f"/schedules/{existing[name]['id']}", {"name": name, "manifest": manifest})
        else:
            existing[name] = call("POST", "/schedules", {"agent_name": "support-triage", "name": name, "manifest": manifest})["data"]
        print("schedule", name, cron)
    return existing


def main():
    upsert_mcp_servers()
    for f in sorted((ROOT / "agents").glob("*.json")):
        upsert_agent(resolve(json.loads(f.read_text())))
    schedules = upsert_schedules()
    if sys.argv[1:] == ["run"]:
        run = call("POST", "/schedules/runs", {"schedule_id": schedules["triage-on-the-hour"]["id"]})
        print("triage run started:", run["data"])


if __name__ == "__main__":
    main()
