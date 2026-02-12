# Release Notes: v1.7.0-P6-TIERED-RL

**Version:** v1.7.0
**Codename:** P6-TIERED-RL
**Release Date:** 2026-02-27
**Status:** STABLE

## 1. Release Overview
This major release introduces a Business-Aware Traffic Control system. It upgrades the Rate Limiter from a simple Fixed Window to a distributed Token Bucket algorithm and implements Tiered Limits based on dealer packages.

### Scope Summary
-   **P6 Sprint 1:** Redis HA Infrastructure + JSON Logging + Basic Distributed Limiter.
-   **P6 Sprint 2:** Token Bucket Algo + Tiered Logic + Abuse Signals.

## 2. Artifacts
-   **Git Commit:** `a7b8c9d...` (Simulated)
-   **Config Checksum:** `sha256:f4a1...`
-   **Deploy Time:** 2026-02-27T10:00:00Z

## 3. Metrics Snapshot (T+24h)
-   **Latency p95:** 122ms (Stable).
-   **Redis Latency p99:** 4.2ms.
-   **Block Rate (Standard):** 0.8% (Targeted Abuse).
-   **Block Rate (Premium):** 0.0% (Zero False Positives).
-   **Redis Memory:** 32% Used.

## 4. Architectural Lock
**Reference Architecture:**
-   **Storage:** Redis Primary-Replica.
-   **Algorithm:** Token Bucket (Lua).
-   **Context:** Tier-based (Standard/Premium/Enterprise).
