# Open Risk Register (P6 Start)

**Date:** 2026-02-12

| ID | Risk | Severity | Mitigation Status | Owner |
|:---|:---|:---|:---|:---|
| **R-001** | **In-Memory Rate Limiter:** Scaling backend replicas multiplies the allowed rate limit (e.g., 2 pods = 2x limit). | Medium | **Accepted for P5.** Planned migration to Redis in P6 Sprint 1. | Backend Lead |
| **R-002** | **Unstructured Logs:** Analyzing incidents requires regex parsing text logs. | Medium | Planned `structlog` migration in P6 Sprint 1. | DevOps |
| **R-003** | **Alert Thresholds:** Alerts might be noisy (false positives) initially. | Low | Tuned during Hypercare (T+24h). | SRE |
| **R-004** | **Stripe Keys:** Keys currently loaded from Env Vars. No rotation policy. | Low | Backlog: Secret Manager integration (P7). | Security |
| **R-005** | **Pricing Config:** Manual config entry via Admin is error-prone. | Medium | Backlog: Config Validation/Simulation UI (P7). | Product |
