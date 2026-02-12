# P6 Phase Scope: Observability & Optimization

**Start Date:** TBD
**Goal:** Achieve high-resolution visibility into system behavior and support horizontal scaling.

## 1. Objectives
1.  **Deep Observability:** Trace every pricing decision and error. Eliminate "black box" support tickets.
2.  **Distributed Scalability:** Move stateful components (Rate Limiter) out of application memory.
3.  **Proactive Monitoring:** Dashboarding for business metrics (Revenue, Churn) and system metrics (Latency, Errors).

## 2. Key Deliverables
-   **Structured Logging:** JSON logs with Correlation IDs.
-   **Distributed Rate Limiting:** Redis-backed implementation.
-   **Metrics Exporter:** Prometheus endpoint (`/metrics`) or OpenTelemetry integration.
-   **Admin Dashboard V2:** Visualizing Pricing/Expiry health.

## 3. Tech Debt (to address)
-   In-Memory Rate Limiter (Main Blocker for K8s Scaling).
-   Lack of persistent Audit Log storage policy (Archival).
