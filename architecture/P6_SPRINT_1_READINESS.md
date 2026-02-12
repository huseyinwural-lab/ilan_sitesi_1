# P6 Sprint 1 Readiness Checklist

**Goal:** Prepare for Distributed Rate Limiting & Observability.

## 1. Infrastructure (Redis)
- [ ] **Decision:** Managed Redis (AWS ElastiCache / Render Redis / Azure MemoryStore).
- [ ] **Network:** Security Group allows Inbound TCP 6379 from Backend Pods only.
- [ ] **Auth:** Redis Password/Token available in Vault/Env (`REDIS_URL`).

## 2. Observability Pipeline
- [ ] **Ingestion:** Log Aggregator (Datadog/Splunk/ELK) endpoint ready.
- [ ] **Standard:** `X-Request-ID` (Correlation ID) propagation logic defined (Nginx -> Backend).

## 3. Development Environment
- [ ] **Local:** `docker-compose.yml` updated to include `redis` service.
- [ ] **Libs:** `redis-py` and `structlog` added to `requirements.txt`.
