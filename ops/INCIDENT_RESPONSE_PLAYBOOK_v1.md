# Incident Response Playbook

**Document ID:** INCIDENT_RESPONSE_PLAYBOOK_v1  
**Date:** 2026-02-13  
**Status:** 🚨 ACTIVE  

---

## 1. Billing Incidents

### Scenario A: Payment Succeeded, Quota Not Unlocked
**Severity:** SEV-2
**Action:**
1. Check Stripe Webhook logs (`POST /webhook` 200 OK?).
2. If webhook failed/missing, check Backend Logs for signature error.
3. **Fix:** Manually create/update `UserSubscription` in DB.
4. **Communicate:** Email user "Activated manually, sorry for delay".

### Scenario B: Double Charge
**Severity:** SEV-2
**Action:**
1. Refund duplicate in Stripe.
2. Check `StripeEvent` table for idempotency failure.

---

## 2. Performance Incidents

### Scenario C: Search Latency Spike > 1s
**Severity:** SEV-2
**Action:**
1. Check Database CPU.
2. If 100%, **Enable Aggressive Rate Limit** (30 req/min).
3. If Redis Down, restart Redis Container (Fail-open logic allows DB hit but slow).

---

## 3. Security

### Scenario D: Mass Signup Spam
**Severity:** SEV-1
**Action:**
1. Disable `/register` endpoint temporarily.
2. Invalidate all unused Invite Codes.
3. Purge spam users via `DELETE FROM users WHERE ...`.
