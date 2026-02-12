# Log Pipeline Validation Checklist

**Component:** Structured Logging (JSON)
**Role:** Observability & Debugging

## 1. Ingestion Validation
- [ ] **Format:** Log aggregator successfully parses JSON lines.
- [ ] **Fields:** Verify presence of mandatory fields in random sample:
    -   `timestamp` (ISO8601)
    -   `level` (INFO/WARN/ERROR)
    -   `service` ("backend")
    -   `request_id` (UUID)
    -   `message` or `event`

## 2. Completeness
- [ ] **Coverage:** Logs received from all active pods.
- [ ] **Context:** `user_id` present in authenticated request logs.
- [ ] **Trace:** `price_source` field present in Pricing logs.

## 3. Retention & Cost
- [ ] **Policy:** Retention set to 30 Days (Hot), 1 Year (Archive/S3).
- [ ] **Volume Est:** Estimated ~5GB/day @ 100 req/sec.
- [ ] **Cost Impact:** Within budget.

## 4. Alerting
- [ ] **Rule Test:** Manually trigger an `ERROR` log. Verify Alert triggers.
- [ ] **Rule Test:** Manually trigger a high volume of logs. Verify "Volume Anomaly" alert (if config).
