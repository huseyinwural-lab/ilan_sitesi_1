#!/usr/bin/env bash
set -euo pipefail

EVIDENCE_FILE="/app/ops/SMOKE_FINAL01_STAGING_EVIDENCE.md"
: > "$EVIDENCE_FILE"

log() {
  echo "$1" | tee -a "$EVIDENCE_FILE"
}

fail() {
  log "\nSTATUS: FAIL"
  exit 1
}

trap 'fail' ERR

log "# SMOKE_FINAL01_STAGING_EVIDENCE"
log "Run (UTC): $(date -u +\"%Y-%m-%dT%H:%M:%SZ\")"
log ""

: "${STAGING_BASE_URL:?STAGING_BASE_URL gerekli}"
: "${DATABASE_URL:?DATABASE_URL gerekli}"
: "${ADMIN_EMAIL:?ADMIN_EMAIL gerekli}"
: "${ADMIN_PASSWORD:?ADMIN_PASSWORD gerekli}"
: "${DEALER_EMAIL:?DEALER_EMAIL gerekli}"
: "${DEALER_PASSWORD:?DEALER_PASSWORD gerekli}"
: "${CONSUMER_EMAIL:?CONSUMER_EMAIL gerekli}"
: "${CONSUMER_PASSWORD:?CONSUMER_PASSWORD gerekli}"
: "${STRIPE_WEBHOOK_SECRET:?STRIPE_WEBHOOK_SECRET gerekli}"

if ! command -v psql > /dev/null 2>&1; then
  log "psql bulunamadı. Staging smoke için psql gerekir."
  exit 2
fi

json_get() {
  python - <<'PY'
import json,sys
payload = json.loads(sys.argv[1])
path = sys.argv[2].split('.')
value = payload
for key in path:
    if isinstance(value, dict):
        value = value.get(key)
    else:
        value = None
        break
print(value if value is not None else "")
PY
}

log "## 1) Admin Login"
admin_resp=$(curl -s -X POST "$STAGING_BASE_URL/api/auth/login" -H "Content-Type: application/json" \
  -d "{\"email\":\"$ADMIN_EMAIL\",\"password\":\"$ADMIN_PASSWORD\"}")
admin_token=$(json_get "$admin_resp" "access_token")
if [[ -z "$admin_token" ]]; then
  log "Admin login failed: $admin_resp"
  exit 1
fi

log "## 2) Dealer Login"
dealer_resp=$(curl -s -X POST "$STAGING_BASE_URL/api/auth/login" -H "Content-Type: application/json" \
  -d "{\"email\":\"$DEALER_EMAIL\",\"password\":\"$DEALER_PASSWORD\"}")
dealer_token=$(json_get "$dealer_resp" "access_token")
dealer_id=$(json_get "$dealer_resp" "user.id")
if [[ -z "$dealer_token" || -z "$dealer_id" ]]; then
  log "Dealer login failed: $dealer_resp"
  exit 1
fi

log "## 3) Consumer Login"
consumer_resp=$(curl -s -X POST "$STAGING_BASE_URL/api/auth/login" -H "Content-Type: application/json" \
  -d "{\"email\":\"$CONSUMER_EMAIL\",\"password\":\"$CONSUMER_PASSWORD\"}")
consumer_token=$(json_get "$consumer_resp" "access_token")
consumer_id=$(json_get "$consumer_resp" "user.id")
if [[ -z "$consumer_token" || -z "$consumer_id" ]]; then
  log "Consumer login failed: $consumer_resp"
  exit 1
fi

log "## 4) Subscription + Invoice (SQL)"
plan_slug="${PLAN_SLUG:-dealer-pro-monthly}"
plan_id=$(psql "$DATABASE_URL" -t -c "SELECT id FROM plans WHERE slug='${plan_slug}' LIMIT 1;" | tr -d '[:space:]')
if [[ -z "$plan_id" ]]; then
  log "Plan bulunamadı: $plan_slug"
  exit 1
fi

sub_id=$(python - <<'PY'
import uuid
print(uuid.uuid4())
PY
)

psql "$DATABASE_URL" -c "INSERT INTO user_subscriptions (id, user_id, plan_id, status, created_at, current_period_start, current_period_end, provider) VALUES ('$sub_id', '$dealer_id', '$plan_id', 'pending', now(), now(), now() + interval '30 days', 'stripe');"

invoice_resp=$(curl -s -X POST "$STAGING_BASE_URL/api/admin/invoices" -H "Content-Type: application/json" \
  -H "Authorization: Bearer $admin_token" \
  -d "{\"user_id\":\"$dealer_id\",\"subscription_id\":\"$sub_id\",\"plan_id\":\"$plan_id\",\"amount_total\":49.99,\"currency\":\"EUR\",\"issue_now\":true}")

invoice_id=$(json_get "$invoice_resp" "invoice.id")
if [[ -z "$invoice_id" ]]; then
  invoice_id=$(json_get "$invoice_resp" "id")
fi
if [[ -z "$invoice_id" ]]; then
  log "Invoice create failed: $invoice_resp"
  exit 1
fi

log "## 5) Checkout Session"
checkout_resp=$(curl -s -X POST "$STAGING_BASE_URL/api/payments/create-checkout-session" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $dealer_token" \
  -d "{\"invoice_id\":\"$invoice_id\",\"origin_url\":\"$STAGING_BASE_URL\"}")

session_id=$(json_get "$checkout_resp" "session_id")
if [[ -z "$session_id" ]]; then
  log "Checkout failed: $checkout_resp"
  exit 1
fi
log "Checkout session_id: $session_id"

log "## 6) Webhook (deterministic)"
python - <<PY
import json, time, hmac, hashlib
from pathlib import Path
secret = "$STRIPE_WEBHOOK_SECRET"
session_id = "$session_id"
invoice_id = "$invoice_id"

event = {
  "id": "evt_smoke_1",
  "type": "checkout.session.completed",
  "data": {
    "object": {
      "id": session_id,
      "payment_status": "paid",
      "metadata": {
        "invoice_id": invoice_id,
        "dealer_id": "$dealer_id",
        "invoice_no": "SMOKE-INV-001"
      }
    }
  }
}
body = json.dumps(event)
nonce = int(time.time())
signed = f"{nonce}.{body}"
signature = hmac.new(secret.encode(), signed.encode(), hashlib.sha256).hexdigest()
header = f"t={nonce},v1={signature}"
Path('/tmp/stripe_event_smoke.json').write_text(body, encoding='utf-8')
Path('/tmp/stripe_signature_smoke.txt').write_text(header, encoding='utf-8')
PY

SIG=$(cat /tmp/stripe_signature_smoke.txt)
webhook_resp=$(curl -s -X POST "$STAGING_BASE_URL/api/webhook/stripe" -H "stripe-signature: $SIG" -H "Content-Type: application/json" --data-binary @/tmp/stripe_event_smoke.json)
log "Webhook response: $webhook_resp"

log "## 7) Payment Assertions"
invoice_status=$(psql "$DATABASE_URL" -t -c "SELECT status FROM admin_invoices WHERE id='${invoice_id}';" | tr -d '[:space:]')
subscription_status=$(psql "$DATABASE_URL" -t -c "SELECT status FROM user_subscriptions WHERE id='${sub_id}';" | tr -d '[:space:]')
listing_quota=$(psql "$DATABASE_URL" -t -c "SELECT listing_quota_limit FROM users WHERE id='${dealer_id}';" | tr -d '[:space:]')

log "Invoice status: $invoice_status"
log "Subscription status: $subscription_status"
log "Listing quota: $listing_quota"

[[ "$invoice_status" == "paid" ]] || exit 1
[[ "$subscription_status" == "active" ]] || exit 1

log "## 8) Duplicate Webhook"
dup_resp=$(curl -s -X POST "$STAGING_BASE_URL/api/webhook/stripe" -H "stripe-signature: $SIG" -H "Content-Type: application/json" --data-binary @/tmp/stripe_event_smoke.json)
log "Duplicate response: $dup_resp"

log "## 9) Listing Create / Submit / Approve"
category_id=$(psql "$DATABASE_URL" -t -c "SELECT id FROM categories ORDER BY created_at LIMIT 1;" | tr -d '[:space:]')
make_id=$(psql "$DATABASE_URL" -t -c "SELECT id FROM vehicle_makes ORDER BY created_at LIMIT 1;" | tr -d '[:space:]')
model_id=$(psql "$DATABASE_URL" -t -c "SELECT id FROM vehicle_models WHERE make_id='${make_id}' ORDER BY created_at LIMIT 1;" | tr -d '[:space:]')

if [[ -z "$category_id" || -z "$make_id" || -z "$model_id" ]]; then
  log "Category/Make/Model bulunamadı. Seed gerekli olabilir."
  exit 1
fi

listing_resp=$(curl -s -X POST "$STAGING_BASE_URL/api/v1/listings/vehicle" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $consumer_token" \
  -d "{\"title\":\"Smoke Listing\",\"description\":\"Smoke listing description\",\"price\":{\"amount\":15000,\"currency_primary\":\"EUR\"},\"country\":\"DE\",\"category_id\":\"$category_id\",\"make_id\":\"$make_id\",\"model_id\":\"$model_id\"}")

listing_id=$(json_get "$listing_resp" "id")
if [[ -z "$listing_id" ]]; then
  log "Listing create failed: $listing_resp"
  exit 1
fi

python - <<'PY'
from PIL import Image
img = Image.new('RGB', (800, 600), color=(120, 180, 240))
img.save('/tmp/smoke_listing.jpg', format='JPEG')
PY

curl -s -X POST "$STAGING_BASE_URL/api/v1/listings/vehicle/$listing_id/media" \
  -H "Authorization: Bearer $consumer_token" \
  -F "files=@/tmp/smoke_listing.jpg" > /dev/null

submit_resp=$(curl -s -X POST "$STAGING_BASE_URL/api/v1/listings/vehicle/$listing_id/submit" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $consumer_token" -d '{}')

log "Submit response: $submit_resp"

approve_resp=$(curl -s -X POST "$STAGING_BASE_URL/api/admin/listings/$listing_id/approve" \
  -H "Authorization: Bearer $admin_token")
log "Approve response: $approve_resp"

log "## 10) Search Visibility"
search_resp=$(curl -s "$STAGING_BASE_URL/api/v2/search?country=DE")
if [[ "$search_resp" != *"$listing_id"* ]]; then
  log "Listing search visibility FAILED"
  exit 1
fi

log "\nSTATUS: PASS"
