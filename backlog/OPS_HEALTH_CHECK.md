# Backlog: Operational Health Check (OPS-HC)

**Priority:** P5 (Critical for Operations)
**Owner:** Operations / DevOps

## Problem
With the new "Fail-Fast" pricing engine, missing database configurations (VAT, PriceConfig) will immediately block revenue generation (Listing Creation). We need a proactive way to detect these gaps before users encounter them.

## Requirement
Create an automated "Health Check" that verifies the integrity of the pricing configuration for all enabled countries.

## Check Criteria
For every `Country` where `is_enabled = True`:
1.  [ ] **VAT Rate:** Is there an active `VatRate` (standard)?
2.  [ ] **Currency Map:** Is there a `CountryCurrencyMap` entry?
3.  [ ] **Dealer Price:** Is there an active `PriceConfig` for `segment=dealer` + `type=pay_per_listing`?
4.  [ ] **Free Quota:** (Warning only) Is there a `FreeQuotaConfig`?

## Deliverables
1.  **API Endpoint:** `GET /api/admin/health/pricing`
    - Returns JSON report:
      ```json
      {
        "status": "warning",
        "issues": [
          {"country": "IT", "error": "Missing VAT Rate"},
          {"country": "FR", "error": "Missing Price Config"}
        ]
      }
      ```
2.  **Dashboard Widget:** Admin Panel > Dashboard shows a "Config Status" indicator (Green/Red).
3.  **Alerting:** (Future) Integration with Slack/Email if status is Red.

## Action Plan
1.  Add logic to `app/routers/audit.py` or `admin.py`.
2.  Frontend: Add simple fetch & display on Admin Dashboard.
