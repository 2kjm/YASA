#!/bin/sh
# Start TrueForge with the Freshdesk MCP host allowlisted. Its SSRF guard blocks hosts resolving to private or NAT64
# ranges (Freshdesk on IPv6-only/NAT64 networks).
# Only FRESHDESK_DOMAIN is read from .env: the sandbox may inherit this process's environment, so no secrets here.
cd "$(dirname "$0")/.." || exit 1
domain=$(grep '^FRESHDESK_DOMAIN=' .env | cut -d= -f2)
OUTBOUND_URL_ALLOWED_HOSTS="[\"$domain\"]" exec npx -y @truefoundry/trueforge@latest
