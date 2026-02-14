# Revenue Validation Report

**Document ID:** REVENUE_VALIDATION_REPORT_v1  
**Date:** 2026-02-13  
**Status:** 🏗️ PLANNED  

---

## 1. Reconciliation Queries

### 1.1. Active Subscriptions Check
```sql
SELECT count(*) as db_active_count 
FROM user_subscriptions 
WHERE status = 'active';
```
*Compare with Stripe Dashboard -> Customers -> Subscriptions -> Active.*

### 1.2. Payment Integrity
```sql
SELECT count(*) 
FROM payment_attempts 
WHERE status = 'succeeded';
```
*Compare with Stripe Dashboard -> Payments -> Succeeded.*

## 2. Webhook Health
- **Check Logs:** `grep "Webhook Error" /var/log/supervisor/backend.out.log`
- **Target:** 0 Errors.

## 3. Discrepancy Action Plan
If `db_active_count != stripe_active_count`:
1. Identify missing user via Stripe Customer ID.
2. Check `StripeEvent` table for missing webhook.
3. Replay webhook via Stripe CLI.
4. If failed, manual fix via Admin API.
