# Production Monitoring Baseline

**Document ID:** PRODUCTION_MONITORING_BASELINE_v1  
**Date:** 2026-02-13  
**Status:** 🏗️ PLANNED  

---

## 1. Key Metrics

### 1.1. Business Metrics
- **ARR (Annual Recurring Revenue):** Sum of active subscriptions.
- **Churn Rate:** Canceled subscriptions / Total active.
- **Conversion Rate:** Checkout Success / Pricing Page Views.

### 1.2. Operational Metrics
- **Payment Success Rate:** `invoice.payment_succeeded` / Total Invoices.
- **Webhook Latency:** Time to process webhook event (Target < 2s).
- **Quota Rejections:** Count of `403 QUOTA_EXCEEDED` responses.

## 2. Alert Rules

| Severity | Metric | Threshold | Action |
|---|---|---|---|
| **Critical** | `webhook_error_rate` | > 5% (5m window) | Page On-Call (Revenue at risk) |
| **High** | `5xx_error_rate` | > 1% | Notify Engineering |
| **Medium** | `quota_block_rate` | > 20% | Check UX / Abuse |

## 3. Implementation
- **Logging:** Structured JSON logs for all Payment/Quota events.
- **Dashboard:** Grafana/CloudWatch view aggregating logs.
