# P23: Enterprise Readiness & Multi-Tenant Analysis

## 1. Dynamic Configuration Policy
To support enterprise agility, hardcoded values (weights, thresholds) must move to the database.

### 1.1. Schema: `system_configs`
| Column | Type | Example Key | Example Value |
| :--- | :--- | :--- | :--- |
| `key` | String (PK) | `ranking_weights_v1` | `{"view": 1, "contact": 10, "fav": 5}` |
| `value` | JSONB | `ml_thresholds` | `{"min_score": 0.1, "timeout_ms": 100}` |
| `description` | String | - | "Weights for Hybrid Ranking" |

### 1.2. Usage
*   **Caching**: Configs should be cached in Redis for 5 minutes.
*   **Audit**: Every update to `system_configs` MUST generate an `audit_logs` entry.

## 2. Multi-Tenant Readiness Assessment

### 2.1. Current State: "Country as Tenant"
The current architecture uses `Country` (`DE`, `TR`, `FR`) as the primary isolation layer.
*   **Pros**: Simple, fits the "Global Classifieds" use case perfectly.
*   **Cons**: Cannot easily sell the software to *another company* (SaaS) who wants their own `TR` market isolated from ours.

### 2.2. Gap Analysis for SaaS (True Multi-Tenancy)
To become a SaaS platform (e.g., "Shopify for Classifieds"):
1.  **Database**: Need `tenant_id` column on **ALL** tables (Users, Listings, Orders).
2.  **Infrastructure**: Row-Level Security (RLS) in PostgreSQL is required to enforce isolation at the DB layer.
3.  **Auth**: Authorization must include `tenant_id` scope (e.g., User A is Admin in Tenant X, but User B in Tenant Y).

### 2.3. Verdict
*   **Current Status**: **Single-Tenant, Multi-Region**.
*   **Enterprise Fit**: Ready for a single global corporation.
*   **SaaS Fit**: Requires P24 "SaaS Refactoring" (High effort).

## 3. Enterprise Audit Trail
We have extended the `AuditLog` coverage to include:
*   `ML_MODEL_SWITCH`: When a model is activated/deactivated.
*   `EXPERIMENT_OVERRIDE`: When traffic allocation changes.
*   `CONFIG_CHANGE`: When ranking weights are tuned.
