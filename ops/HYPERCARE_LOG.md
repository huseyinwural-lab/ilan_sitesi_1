# Hypercare Monitoring Log (T+24h)

**Start Time:** Deployment Complete
**End Time:** T+24 Hours
**Owner:** On-Call SRE

## 1. Hourly Check Targets

| Metric | Target | Action if Breached |
| :--- | :--- | :--- |
| **Fail-Fast Rate (409)** | 0% | Immediate Config Check. Check `PriceConfig` for failing country. |
| **Block Rate (429)** | < 1% | Analyze IP list. If legit user, consider loosening `RL_DEFAULT`. |
| **Publish Success** | > 98% | Check logs for 500s or DB Lock timeouts. |
| **Latency p95** | < 500ms | Check DB CPU and connection pool. |

## 2. Event Log
| Time (UTC) | Metric Status | Anomalies Observed | Action Taken |
| :--- | :--- | :--- | :--- |
| T+1h | 🟢 Nominal | None | None |
| T+4h | | | |
| T+8h | | | |
| T+12h| | | |
| T+24h| | | |

## 3. Expiry Job Verification
- [ ] **Job Run Time:** 00:00 UTC
- [ ] **Status:** Success (Exit Code 0)
- [ ] **Log:** "Expired X subscriptions" found in logs.
