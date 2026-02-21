#!/usr/bin/env bash
set -euo pipefail

EVIDENCE_FILE="/app/ops/SMOKE_STRIPE_STAGING_EVIDENCE.md"
: > "$EVIDENCE_FILE"

log() {
  echo "$1" | tee -a "$EVIDENCE_FILE"
}

log "# SMOKE_STRIPE_STAGING_EVIDENCE"
log "Run (UTC): $(date -u +\"%Y-%m-%dT%H:%M:%SZ\")"
log ""

: "${STAGING_BASE_URL:?STAGING_BASE_URL gerekli}"
: "${STRIPE_WEBHOOK_SECRET:?STRIPE_WEBHOOK_SECRET gerekli}"

log "## Stripe CLI forward (opsiyonel)"
log "Komut: stripe listen --forward-to ${STAGING_BASE_URL}/api/webhook/stripe"
log ""
log "## Deterministic webhook info"
log "Stripe CLI yoksa smoke_final01_staging.sh deterministic webhook ile zinciri doğrular."
log "
STATUS: INFO"
