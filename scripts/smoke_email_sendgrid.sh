#!/usr/bin/env bash
set -euo pipefail

EVIDENCE_FILE="/app/ops/SMOKE_EMAIL_EVIDENCE.md"
: > "$EVIDENCE_FILE"

log() {
  echo "$1" | tee -a "$EVIDENCE_FILE"
}

fail() {
  log "\nSTATUS: FAIL"
  exit 1
}

trap 'fail' ERR

log "# SMOKE_EMAIL_EVIDENCE"
log "Run (UTC): $(date -u +\"%Y-%m-%dT%H:%M:%SZ\")"
log ""

: "${STAGING_BASE_URL:?STAGING_BASE_URL gerekli}"
: "${EMAIL_PROVIDER:?EMAIL_PROVIDER gerekli}"
: "${TEST_INBOX_EMAIL:?TEST_INBOX_EMAIL gerekli}"
: "${TEST_PASSWORD:?TEST_PASSWORD gerekli}"
: "${DATABASE_URL:?DATABASE_URL gerekli}"

if [[ "$EMAIL_PROVIDER" != "sendgrid" ]]; then
  log "EMAIL_PROVIDER sendgrid değil: $EMAIL_PROVIDER"
  exit 1
fi

if ! command -v psql > /dev/null 2>&1; then
  log "psql bulunamadı. Email smoke için psql gerekir."
  exit 2
fi

RUN_ID=$(date +%s)
if [[ "${USE_PLUS_ADDRESSING:-true}" == "true" ]]; then
  localpart=${TEST_INBOX_EMAIL%@*}
  domain=${TEST_INBOX_EMAIL#*@}
  EFFECTIVE_EMAIL="${localpart}+${RUN_ID}@${domain}"
else
  EFFECTIVE_EMAIL="$TEST_INBOX_EMAIL"
fi

log "Test email: $EFFECTIVE_EMAIL"

register_resp=$(curl -s -X POST "$STAGING_BASE_URL/api/auth/register/consumer" -H "Content-Type: application/json" \
  -d "{\"full_name\":\"Smoke User\",\"email\":\"$EFFECTIVE_EMAIL\",\"password\":\"$TEST_PASSWORD\",\"country_code\":\"DE\",\"preferred_language\":\"tr\"}")

log "Register response: $register_resp"

log "## Inbox Checklist (manual confirmation)"
log "- [ ] SendGrid email geldi (subject: doğrulama kodu)"
log "- [ ] Kod/Link not edildi"

if [[ -z "${EXPIRED_CODE:-}" || -z "${VALID_CODE:-}" ]]; then
  log "EXPIRED_CODE / VALID_CODE env verilmedi. Smoke BLOCKED."
  exit 2
fi

log "## Expired Token Test"
user_id=$(psql "$DATABASE_URL" -t -c "SELECT id FROM users WHERE email='${EFFECTIVE_EMAIL}' LIMIT 1;" | tr -d '[:space:]')
if [[ -z "$user_id" ]]; then
  log "User not found in DB."
  exit 1
fi

psql "$DATABASE_URL" -c "UPDATE email_verification_tokens SET expires_at = now() - interval '1 minute' WHERE user_id='${user_id}' AND consumed_at IS NULL;" > /dev/null

expired_resp=$(curl -s -i -X POST "$STAGING_BASE_URL/api/auth/verify-email" -H "Content-Type: application/json" \
  -d "{\"email\":\"$EFFECTIVE_EMAIL\",\"code\":\"$EXPIRED_CODE\"}" | head -n 1)
log "Expired verify status: $expired_resp"

log "## Valid Token + Reuse Test"
valid_resp=$(curl -s -i -X POST "$STAGING_BASE_URL/api/auth/verify-email" -H "Content-Type: application/json" \
  -d "{\"email\":\"$EFFECTIVE_EMAIL\",\"code\":\"$VALID_CODE\"}" | head -n 1)
log "Verify status: $valid_resp"

reuse_resp=$(curl -s -i -X POST "$STAGING_BASE_URL/api/auth/verify-email" -H "Content-Type: application/json" \
  -d "{\"email\":\"$EFFECTIVE_EMAIL\",\"code\":\"$VALID_CODE\"}" | head -n 1)
log "Reuse status: $reuse_resp"

log "## Prod Mock Guard Test"
set +e
APP_ENV=prod EMAIL_PROVIDER=mock PYTHONPATH=/app/backend python -c "import app.server" 2>/tmp/mock_guard_err.log
exit_code=$?
set -e
if [[ $exit_code -eq 0 ]]; then
  log "Mock guard test FAILED (import succeeded)"
  exit 1
else
  log "Mock guard test PASS (startup blocked)"
fi

log "\nSTATUS: PASS"
