# Rate Limiting Risk Assessment

**Date:** 2026-02-12
**Component:** `app.core.rate_limit.RateLimiter`

## 1. Distributed Environment Risk
**Risk:** The current rate limiter stores counters in application memory (`_rate_limit_store` dict).
-   **Scenario:** If the application runs on 3 replicas (Kubernetes Pods), a user can theoretically hit 3x the limit (e.g., 180 req/min instead of 60).
-   **Impact:** Medium (Acceptable for P5 launch).
-   **Mitigation:**
    -   Use "Sticky Sessions" at Load Balancer level (ensures user hits same pod).
    -   Plan P6 migration to Redis-based limiter (Global State).

## 2. Horizontal Scaling
**Risk:** Scaling out significantly increases total allowed throughput for attackers distributed across IPs.
-   **Impact:** Low (Tier 1 is user-based, so authenticating on multiple pods still limits per user effectively if sticky sessions work, otherwise limits are multiplied).

## 3. IP Verification (Spoofing)
**Risk:** `request.client.host` might return the Load Balancer IP or be spoofed if headers aren't trusted.
-   **Impact:** High (All users share same IP -> Global Block).
-   **Mitigation:**
    -   Ensure `uvicorn` or `gunicorn` is configured with `--proxy-headers`.
    -   Validate `X-Forwarded-For` from trusted downstreams only (e.g., Cloudflare/Ingress).

## 4. Auth vs Rate Limit Order
**Risk:** If Rate Limit runs *before* Auth, attackers can flood with invalid tokens to block legitimate IPs.
**Current State:** Rate Limit runs as dependency. It checks `Authorization` header structure. If valid-looking, it uses Token bucket. If invalid, it uses IP bucket.
-   **Assessment:** Acceptable.
