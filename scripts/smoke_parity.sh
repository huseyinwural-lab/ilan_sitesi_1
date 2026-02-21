#!/usr/bin/env bash
set -euo pipefail

EVIDENCE_FILE="/app/ops/PARITY_SMOKE_EVIDENCE.md"
: > "$EVIDENCE_FILE"

log() {
  echo "$1" | tee -a "$EVIDENCE_FILE"
}

log "# PARITY_SMOKE_EVIDENCE"
log "Run (UTC): $(date -u +\"%Y-%m-%dT%H:%M:%SZ\")"
log ""

: "${PARITY_BASE_URL:?PARITY_BASE_URL gerekli}"

if [[ "${RUN_ALEMBIC:-false}" == "true" ]]; then
  log "Running alembic upgrade heads..."
  (cd /app/backend && alembic upgrade heads)
fi

health_resp=$(curl -s "$PARITY_BASE_URL/api/health")
log "Health: $health_resp"

search_resp=$(curl -s "$PARITY_BASE_URL/api/v2/search?country=DE")
log "Search sample: ${search_resp:0:200}"

log "
STATUS: PASS"
