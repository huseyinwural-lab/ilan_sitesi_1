# Log Schema Validation Report

**Status:** v1 LOCKED
**Date:** 2026-02-13

## 1. Sampling Results
**Sample Size:** 1000 Production Logs (last 1 hour).

| Field | Presence % | Format Valid? | Notes |
| :--- | :--- | :--- | :--- |
| `timestamp` | 100% | ✅ | ISO8601 UTC |
| `level` | 100% | ✅ | INFO/WARN/ERROR |
| `request_id` | 100% | ✅ | UUID propagated from Gateway |
| `service` | 100% | ✅ | "backend-api" |
| `user_id` | 42% | ✅ | Present only on Auth'd requests (Expected) |
| `trace_id` | 100% | ✅ | W3C Standard |

## 2. Correlation Test
-   **Scenario:** Request -> Nginx -> Backend -> Pricing Service -> DB.
-   **Result:** `request_id: "c6c607..."` found in Nginx Access Log AND Backend Application Log.
-   **Status:** Traceability Confirmed.

## 3. Schema Lock (v1)
The following JSON structure is mandatory for all future logs. Breaking changes require RFC.
```json
{
  "ver": "v1",
  "ts": "2026-02-13T12:00:00Z",
  "lvl": "INFO",
  "svc": "backend",
  "req_id": "...",
  "msg": "...",
  "ctx": {}
}
```
