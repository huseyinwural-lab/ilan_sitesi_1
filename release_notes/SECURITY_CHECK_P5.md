# Security Sanity Check Report (P5)

**Date:** 2026-02-12
**Reviewer:** Main Agent

## 1. IP Spoofing
- **Check:** Does the Rate Limiter trust headers blindly?
- **Finding:** Currently uses `request.client.host`.
- **Risk:** If behind proxy (Nginx/LB), this is the LB IP.
- **Remediation:** Middleware must be configured to parse `X-Forwarded-For` from trusted proxies (`ForwardedAllowIPS` in Uvicorn). **Added to Prod Checklist.**

## 2. Auth vs Rate Limit Sequence
- **Check:** `Depends(limiter)` vs `Depends(get_current_user)`.
- **Finding:**
    - Dependencies in FastAPI run based on declaration order or graph.
    - Our implementation inspects `Authorization` header *manually* inside Limiter to determine Tier.
    - **Verdict:** Safe. It doesn't wait for full DB User fetch to block brute force (Efficiency win).

## 3. Brute Force Lockout
- **Check:** Does 429 block accounts or IPs?
- **Finding:** Blocks IP for Login endpoints.
- **Gap:** Distributed Botnet (different IPs) could try same account.
- **Backlog:** Implement "Account Lockout" (failed attempts > 5 -> lock account for 15min) in P6.

## 4. Pricing Integrity
- **Check:** Can user manipulate price?
- **Finding:** No. Price is strictly server-side derived. User input for price/currency is ignored/overwritten.
- **Verdict:** Secure.
