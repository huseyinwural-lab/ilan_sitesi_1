# Release Notes: v1.8.0-P7-FINAL

**Version:** v1.8.0
**Codename:** P7-FINAL
**Release Date:** 2026-03-14
**Status:** GOLD / FINAL

## 1. Overview
This is the final planned release of the project. It delivers the complete Admin UI for managing the Tiered Rate Limiting system, comprehensive Health Dashboards, and finalized Security/Audit controls.

## 2. New Features (Admin)
-   **Tier Management:** GUI for upgrading/downgrading Dealer Tiers.
-   **Traffic Monitor:** Real-time visibility into blocked requests and abuse patterns.
-   **System Health:** Live status of Redis, DB, and Cron Jobs.
-   **Abuse Tools:** Manual Override and Investigation panels.

## 3. Improvements
-   **UI/UX:** Complete visual overhaul (Theming, Responsive).
-   **Security:** Hardened RBAC for sensitive admin actions.
-   **Code:** Cleanup of all P6 feature flags and legacy limiters.

## 4. Metrics Snapshot
-   **Status:** Stable.
-   **Test Coverage:** 88%.
-   **Known Issues:** None blocking.

## 5. Deployment
-   **Strategy:** Standard Rolling Update.
-   **Migrations:** None (UI/API logic only).
