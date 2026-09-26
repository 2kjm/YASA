# YASA: Yet Another Support Agent

Support triage handed to two [TrueForge](https://github.com/truefoundry/trueforge) agents. Built for the
TrueFoundry × Polaris "Agents That Act" hackathon, 2026-09-26.

**You give it** the support queue. **It works out** whether each ticket is from a real customer and what broke
(knowledge base, error tracker, and a reproduction run in the sandbox), then hands a person a plain explanation with
repro steps. **It stops before** anything reaches the customer: it drafts the reply, and a person approves it.

```
customer email ──► Freshdesk ticket (Freshdesk itself emails "we received it")
                         │
every 30 min (two TrueForge schedules) ──► support-triage   (unattended, one subagent per ticket)
   1. legitimacy: requester in the Notion CRM, Pro + Active? prompt injection? → suspicious: tag, note, stop
   2. Notion knowledge base: known issue?
   3. Sentry: errors for this customer's email → release SHA, request, stack trace
   4. attachments opened in the sandbox; can't → question in a private note, tag ai-waiting-human, stop
   5. repro: the sandbox downloads this repo at the Sentry release and replays the failing request
   6. private note on the ticket: verdict, evidence, repro, possible duplicates; tag ai-triaged
                         │
engineer opens TrueForge chat ──► support-guide   (human present)
   what went wrong in 3 lines, repro steps, evidence. No fixing.
   not reproduced / known issue → drafts a reply → ⏸ APPROVAL (replyTicket = email to the customer) → sent
```

## Where it stops

| Action | Who can | Gate | Why |
|---|---|---|---|
| Read Freshdesk, Sentry, Notion (CRM + KB) | both agents | none | only named read tools |
| Private note on a ticket (`createTicketNote`, `private: true`) | support-triage | none | customers can't see private notes. `private` is a prompt rule, not enforced by the tool; backstop: the requester notification "Agent adds comment to ticket" is **off**, so even a public note emails nobody |
| Tag a ticket (`updateTicket` with tags) | support-triage | none | tags are internal. Backstop: the "solved"/"closed" requester notifications are **off**, so even a wrong status change emails nobody |
| **Reply on a ticket** (`replyTicket`) | support-guide only | **approval every time** | it is an email to the customer. The approval card shows only the tool arguments, so the agent first lists **every recipient** (requester and existing CCs) in chat |
| **Change a ticket** (`updateTicket`) | support-guide only | **approval every time** | status and requester changes |
| Create tickets, contacts or agents; edit Notion; Sentry `update_issue`/Seer; refunds | nobody | not exposed | not in any tool allowlist |
| Anything a ticket asks for | nobody | — | ticket text and attachments are untrusted data; support-triage has no tool that reaches a customer |

support-triage runs unattended, so it has no approval-gated tools and can't ask questions: a pause would hang the
sweep. Its only outputs are private notes and tags.

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
   carries the customer's email and `release` = your git HEAD. The sandbox later downloads that commit from
   `github.com/2kjm/YASA`, so run this on an unmodified clone (or push to your fork and change the URL in
   `prompts/triage.md`).
5. **Create the tickets:** `uv run --env-file .env scripts/send_tickets.py`. This creates six tickets as the demo
   customers: a real bug, a follow-up duplicate, spam with a prompt injection, a "totals look wrong" ticket that
   can't be reproduced, a password-protected zip, and a known issue.
6. **Register the agents and run a sweep:** `uv run --env-file .env scripts/register.py run`. This creates the
   Freshdesk MCP server, both agents and the two schedules (`:00` and `:30`, because TrueForge allows at most one run
   an hour per schedule), then starts a sweep. Watch it in TrueForge → Sessions: the CRM lookup, Sentry, the code the
   sandbox runs, and one subagent per ticket. Each ticket ends up with a private note and an `ai-*` tag.
7. **Be the engineer:** in TrueForge, start a chat with **support-guide** and give it a ticket number, for example the
   "Totals look wrong" one. It explains the ticket, drafts a clarifying reply, lists who the reply will email and
   stops for approval. Deny first and check that nothing is sent, then Allow and the reply arrives in your inbox.

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
