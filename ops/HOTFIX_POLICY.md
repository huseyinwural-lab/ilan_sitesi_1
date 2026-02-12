# Hotfix Policy v1

**Effective Date:** Post-Go-Live (v1.5.0)

## 1. Branching Strategy
-   **`main`:** Protected. Production code. Deployments trigger from tags.
-   **`develop` (or feature branches):** P6 Development area.
-   **`hotfix/v1.5.x`:** Created from `main` for critical fixes.

## 2. Allowed Hotfixes (Criteria)
Only deploy to Prod if:
1.  **P0:** System Outage / Crash.
2.  **P1:** Revenue Blocked (e.g., Pricing logic bug).
3.  **P1:** Security Vulnerability.

*All other bugs go to P6 backlog.*

## 3. Process
1.  Create branch `hotfix/fix-name` from `main`.
2.  Implement fix + Regression Test.
3.  PR Review (Mandatory: 1 Approver).
4.  Merge to `main` -> Tag `v1.5.1`.
5.  Deploy.
6.  Backport: Merge `main` into `develop` to keep sync.
