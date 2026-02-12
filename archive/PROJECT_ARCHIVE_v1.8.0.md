# Project Archive (v1.8.0)

**Project:** Admin Panel & Scale Engine
**Completion Date:** 2026-03-15
**Final Version:** v1.8.0

## 1. Architecture Summary
-   **Backend:** FastAPI (Python)
-   **Database:** PostgreSQL (SQLAlchemy + Alembic)
-   **Caching/Limiting:** Redis (Cluster Mode / HA)
-   **Logging:** JSON Structured (structlog) -> ELK/Datadog
-   **Pricing:** Database-Driven Waterfall Engine (T2)

## 2. Critical Decisions Log
-   **Hard Gate:** Pricing is mandatory for publishing. No bypass.
-   **Fail-Open:** If Redis dies, traffic flows (Revenue > Strict Limiting).
-   **UTC:** All systems forced to UTC to ensure Expiry Job consistency.
-   **Tiered Limits:** Business logic determines traffic capacity, not just IP.

## 3. Tech Debt Resolved
-   Removed In-Memory Limiter.
-   Standardized 409/429 Error Responses.
-   Implemented Row-Locking for Concurrency.

## 4. Lessons Learned
-   *Shadow Mode* was critical for tuning Rate Limits without user impact.
-   *Fail-Fast* pricing configuration saved debugging time but requires operational discipline.
-   *Structured Logging* proved essential for correlating 429s with User IDs.

**Status:** ARCHIVED / MAINTENANCE MODE
