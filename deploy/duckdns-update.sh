#!/usr/bin/env bash
# Points your DuckDNS name at this VM's current public IP. Run every 5 minutes from cron (setup-vm.sh installs it).
set -euo pipefail
cd "$(dirname "$0")/.."
set -a; source .env; set +a
curl -fsS "https://www.duckdns.org/update?domains=${DUCKDNS_SUBDOMAIN}&token=${DUCKDNS_TOKEN}&ip=" | grep -q OK \
  || { echo "DuckDNS update failed" >&2; exit 1; }
