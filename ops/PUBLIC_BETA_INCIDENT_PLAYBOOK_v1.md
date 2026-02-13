# Public Beta Incident Playbook

**Document ID:** PUBLIC_BETA_INCIDENT_PLAYBOOK_v1  
**Date:** 2026-02-13  
**Scope:** Search & Detail Page Stability  

---

## 1. Severity Levels

| Level | Description | Example |
|---|---|---|
| **SEV-1 (Critical)** | System Down / Usability Blocked | Database unreachable, API 500s > 10% |
| **SEV-2 (High)** | Major Latency / Partial Failure | Search P95 > 3s, Facets not loading |
| **SEV-3 (Medium)** | Minor Glitch | Incorrect counts, CSS issues |

---

## 2. Response Procedures

### Scenario A: Search Latency Spike (P95 > 2s)
**Diagnosis:** Likely DB CPU saturation due to facet aggregation on cold cache.
**Action:**
1. Check `pg_stat_activity` for stuck queries.
2. **Mitigation:** Temporarily disable Facet Aggregation in API (Feature flag: `ENABLE_FACETS=False`).
   - *Impact:* Filters disappear, but text search remains fast.
3. **Recovery:** Re-enable after traffic subsides or DB scales.

### Scenario B: Database Saturation (Connections Maxed)
**Diagnosis:** `FATAL: remaining connection slots are reserved for non-replication superuser`.
**Action:**
1. Restart Backend Service to flush pool (`supervisorctl restart backend`).
2. **Mitigation:** Reduce Rate Limit to 30 req/min.

### Scenario C: Rate Limit Attack / Scraping
**Diagnosis:** Single IP high RPS.
**Action:**
1. Block IP at Nginx/Firewall level.
2. Verify Redis Rate Limiter is functional.

### Scenario D: Bad Deployment (Rollback)
**Action:**
1. Revert to previous Docker image tag.
2. Run database migration rollback if schema changed (unlikely in Beta).

---

## 3. Communication
- **Internal:** Notify #engineering channel immediately on SEV-1/2.
- **External:** Update Status Page ("System Maintenance") if downtime > 5 mins.

---

## 4. Post-Mortem
Every SEV-1/2 requires a Root Cause Analysis (RCA) document within 24 hours.
