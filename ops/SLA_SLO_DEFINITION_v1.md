# SLA & SLO Definition (v1.0)

**Effective Date:** 2026-03-15

## 1. Service Level Objectives (SLOs)

### A. Availability
| Metric | Target | Measurement Window |
| :--- | :--- | :--- |
| **API Availability** | 99.9% | Monthly |
| **Pricing Engine** | 99.99% | Monthly |
| **Redis Rate Limiter** | 99.5% | Monthly (Fail-open allows app to survive) |

### B. Performance
| Metric | Target |
| :--- | :--- |
| **API Latency (p95)** | < 500ms |
| **Redis Latency (p99)** | < 10ms |
| **Job Duration** | < 10 mins |

### C. Quality
| Metric | Target |
| :--- | :--- |
| **5xx Error Rate** | < 0.1% |
| **False Positive Block Rate** | < 0.01% (Premium Tier) |

## 2. Incident Severity Levels

-   **SEV-1 (Critical):** System Down, Pricing Gate blocking valid requests (409 spike), Security Breach.
    -   *Response:* 15 mins.
-   **SEV-2 (High):** Redis Down (Fail-Open), High Latency, Expiry Job Failed.
    -   *Response:* 1 hour.
-   **SEV-3 (Medium):** Individual User issues, Minor UI bugs in Admin.
    -   *Response:* 4 hours.
-   **SEV-4 (Low):** Cosmetic issues, Non-critical data delays.
    -   *Response:* Next Business Day.
