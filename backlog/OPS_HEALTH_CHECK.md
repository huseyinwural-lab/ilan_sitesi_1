# Ops Health Check v1 Scope (Blocking Gate)

**Priority:** Critical (P0)
**Type:** Blocking Gate for Release/Publish

## 1. Problem Statement
The Pricing Engine adheres to a "Fail-Fast" philosophy. If configurations are missing, the API returns `409 Conflict` and blocks revenue. We must detect these gaps **proactively**.

## 2. Health Check Criteria (Per Active Country)
The system is considered "Healthy" only if ALL enabled countries pass the following checks:

### A. Core Finance
- [ ] **VAT Rate:** Active `standard` rate exists for `[Country]`.
- [ ] **Currency Map:** `CountryCurrencyMap` exists for `[Country]`.

### B. Dealer Segment
- [ ] **Price Config:** Active `PriceConfig` exists for:
  - `country=[Country]`
  - `segment='dealer'`
  - `pricing_type='pay_per_listing'`
  - `is_active=True`
- [ ] **Free Quota:** (Warning) Check if `FreeQuotaConfig` exists. If not, log "Free Quota: 0".

### C. System
- [ ] **Database Connection:** Latency < 100ms.
- [ ] **Stripe Config:** `StripeSettings` exists and `is_enabled=True`.

## 3. Implementation (Ticket OPS-01)
- **Endpoint:** `GET /api/admin/health/pricing`
- **Access:** Super Admin / DevOps.
- **Response:**
  ```json
  {
    "status": "healthy", // or "degraded", "critical"
    "issues": [],
    "matrix": {
      "DE": {"vat": true, "price": true, "quota": true},
      "TR": {"vat": false, "price": false, "quota": false}
    }
  }
  ```

## 4. Alerting Rule
- If `status != 'healthy'` -> Trigger PagerDuty/Slack Alert to Ops Team immediately.
