# Soft Launch Plan

**Document ID:** SOFT_LAUNCH_PLAN_v1  
**Date:** 2026-02-13  
**Status:** 🚀 READY  

---

## 1. Objective
Onboard the first 100 paying customers (or active users) while monitoring system stability and revenue integrity.

## 2. Launch Strategy
**Mode:** Invite Only / Beta Label.

### 2.1. Traffic Control
- **Marketing:** No mass emails yet. Direct outreach to select dealers.
- **Label:** Add "BETA" badge to header.
- **Support:** Direct email (`founders@platform.com`) for billing issues.

### 2.2. Operations Checklist (Daily)
- [ ] Check Stripe Dashboard for failed payments/disputes.
- [ ] Review `quota_usage` vs `listings` count integrity.
- [ ] Monitor Error Logs (Sentry/CloudWatch).

## 3. Incident Response
**Scenario:** User charged but Quota not unlocked.
**Response:**
1. Verify Stripe Payment Intent ID.
2. Manually create `UserSubscription` via DB/Admin API.
3. Investigate Webhook logs.
4. Apologize + Offer 1 month free credit.

---

**Exit Criteria (Public Launch):**
- 100 Active Users.
- Zero Critical Payment Bugs for 7 days.
- Support load manageable.
