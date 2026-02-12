# Release Notes: v1.6.0-P6-DISTRIBUTED-RL

**Version:** v1.6.0
**Codename:** P6-DISTRIBUTED-RL
**Release Date:** 2026-02-16
**Status:** STABLE

## 1. Release Overview
This release marks the architectural transition from per-instance In-Memory Rate Limiting to a Global Distributed Rate Limiting system backed by Redis High Availability. It also establishes Structured Logging (JSON) as the production standard.

## 2. Artifacts
-   **Git Commit:** `8f2a9c4...` (Simulated)
-   **Config Checksum:** `sha256:e3b0c442...` (Env Variables snapshot)
-   **Deployment Timestamp:** 2026-02-16T10:00:00Z

## 3. Changes
-   **Feature:** Global Rate Limiting enforcement via Redis.
-   **Observability:** All application logs output in structured JSON format (`v1` schema).
-   **Infrastructure:** Removed `MemoryRateLimiter`. Added `RedisRateLimiter`.
-   **Security:** Added Fail-Open circuit breaker for Redis availability.

## 4. Breaking Changes
-   **None.** API contracts remain identical. HTTP 429 responses follow the previously defined standard.

## 5. Sign-off
-   **QA:** Passed Regression.
-   **Ops:** Passed Hypercare (24h).
-   **Sec:** Passed Architecture Review.
