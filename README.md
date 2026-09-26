# YASA: Yet Another Support Agent

Support triage handed to two [TrueForge](https://github.com/truefoundry/trueforge) agents. Built for the
TrueFoundry × Polaris "Agents That Act" hackathon, 2026-09-26.

**You give it** the support queue. **It works out** whether each ticket is from a real customer and what broke
(CRM, knowledge base, error tracker), leaves the engineer a private note with repro steps, and drafts the reply.
**It stops before** anything reaches the customer: the reply waits until a person approves it.

```
customer email ──► Freshdesk ticket (Freshdesk itself emails "we received it")
                         │
every 30 min (two TrueForge schedules) ──► support-triage   (one subagent per ticket)
   1. legitimacy: requester in the Notion CRM, Pro + Active? prompt injection? → suspicious: tag, note, stop
   2. Notion knowledge base: known issue?
   3. Sentry: errors for this customer's email → exception, request, release, stack trace
      needs an attachment? → question in a private note, tag ai-waiting-human, stop
   4. private note (Freshdesk emails the engineer): verdict, evidence, repro steps, duplicates, draft reply; tag ai-triaged
   5. ⏸ APPROVAL: replyTicket = email to the customer. The run pauses in TrueForge until a person clicks Allow.
                         │
engineer opens TrueForge chat ──► support-guide   (optional, human present)
   explains a ticket, redrafts a denied reply → ⏸ APPROVAL again
```

## Where it stops

| Action | Who can | Gate | Why |
|---|---|---|---|
| Read Freshdesk, Sentry, Notion (CRM + KB) | both agents | none | only named read tools |
| Private note on a ticket (`createTicketNote`, `private: true`) | support-triage | none | customers can't see private notes; Freshdesk emails the engineer about each one. `private` is a prompt rule, not enforced by the tool; backstop: the requester notification "Agent adds comment to ticket" is **off**, so even a public note emails nobody |
| Tag a ticket (`updateTicket` with tags) | support-triage | none | tags are internal. Backstop: the "solved"/"closed" requester notifications are **off**, so even a wrong status change emails nobody |
| **Reply on a ticket** (`replyTicket`) | both agents | **approval every time** | it is an email to the customer. The approval card shows only the tool arguments, so the agent lists **every recipient** (requester and existing CCs) first: in its note (triage) or in chat (guide) |
| **Change a ticket** (`updateTicket`) | support-guide only | **approval every time** | status and requester changes |
| Create tickets, contacts or agents; edit Notion; Sentry `update_issue`/Seer; refunds | nobody | not exposed | not in any tool allowlist |
| Anything a ticket asks for | nobody | — | ticket text and attachments are untrusted data; the only tool that reaches a customer pauses for a person |

support-triage runs on a schedule. It tags each ticket before drafting the reply, so while one run waits for your
approval, the next run skips that ticket instead of drafting it again.

## Run it

You need Node 20+ (for `npx`), [uv](https://docs.astral.sh/uv/), macOS or Linux, and free accounts on
[Freshdesk](https://www.freshdesk.com) (a trial includes the MCP server), [Sentry](https://sentry.io) and
[Notion](https://notion.so), plus a model key (OpenAI or any provider TrueForge supports).

1. **Configure.** Run `cp .env.example .env` and fill it in. `DEMO_EMAIL_BASE` is an inbox you own: the demo
   customers are its plus-addresses (`you+cafemocha@…`), so every email the demo sends lands with you.
   In Freshdesk go to Admin → Email Notifications → Requester notifications and turn **off** "Agent adds comment to
   ticket", "Agent solves the ticket" and "Agent closes the ticket".
2. **Start TrueForge:** run `scripts/start-trueforge.sh`, then open http://localhost:8790.
   - Settings → Model providers: add your key. Put the model names it lists into `TRIAGE_MODEL` / `GUIDE_MODEL`.
   - MCP servers: connect **Sentry** and **Notion** from the catalog (OAuth).
   - The start script allowlists your Freshdesk host, because TrueForge's SSRF guard blocks hosts that resolve to
     NAT64 addresses on IPv6-only networks.
3. **Seed Notion** (the CRM database "Customers" and the "Knowledge base" pages):
   `uv run --env-file .env scripts/seed_notion.py`. It runs through TrueForge's own Notion connector and refuses to
   create duplicates.
4. **Make real Sentry errors.** Start the demo app and replay the customers' traffic:
   ```sh
   (cd product && uv run --no-project --env-file ../.env --with-requirements requirements.txt uvicorn app:app --port 8765) &
   uv run --env-file .env scripts/traffic.py
   ```
   `product/app.py` has one planted bug: exporting an invoice for "Café Mocha" returns a 500. Each Sentry event
   carries the customer's email and `release` = your git HEAD.
5. **Create the tickets:** `uv run --env-file .env scripts/send_tickets.py`. This creates six tickets as the demo
   customers: a real bug, a follow-up duplicate, spam with a prompt injection, a "totals look wrong" ticket that
   has no Sentry error, a password-protected zip, and a known issue.
6. **Register the agents and run a sweep:** `uv run --env-file .env scripts/register.py run`. This creates the
   Freshdesk MCP server, both agents and the two schedules (`:00` and `:30`, because TrueForge allows at most one run
   an hour per schedule), then starts a sweep. Watch it in TrueForge → Sessions: the CRM lookup, Sentry, one subagent
   per ticket. Each ticket gets a private note (Freshdesk emails `SUPPORT_ENGINEER_EMAIL`) and an `ai-*` tag, then the
   run **pauses on each customer reply**. Deny one and check that nothing is sent; Allow another and it arrives in
   your inbox.
7. **Optional:** start a chat with **support-guide** and give it a ticket number. It explains the ticket and can
   redraft a denied reply, which pauses for approval again.

## Repo

```
agents/     TrueForge agent specs ($VAR from .env, @file from this repo)
prompts/    triage.md, guide.md: the agents' instructions
kb/         the knowledge base pages seeded into Notion
product/    the demo app with its planted bug (app.py) and a self-check (check.py)
scripts/    start-trueforge.sh, seed_notion.py, traffic.py, send_tickets.py, register.py
tickets/    the password-protected attachment for the zip ticket (password bluelotus-2026)
PLAN.md     decisions, rejected alternatives and everything verified while building
```

## AI disclosure

Built on 2026-09-26 with Claude Code (Claude Opus 5.5), which wrote most of the code, prompts and docs under
the builder's direction. The agents themselves run on OpenAI models through TrueForge.
