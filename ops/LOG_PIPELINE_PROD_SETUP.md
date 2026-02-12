# Logging Pipeline Production Setup

**Date:** 2026-02-13
**Component:** OpenSearch / Elasticsearch

## 1. Index Strategy
-   **Pattern:** `app-logs-prod-{yyyy.MM.dd}` (Daily Rollover).
-   **Alias:** `app-logs-prod-write` -> Points to active index.
-   **Template:** `template_app_logs_v1`
    -   `timestamp`: `date` (strict ISO8601)
    -   `request_id`: `keyword`
    -   `user_id`: `keyword`
    -   `data.price`: `float`
    -   `message`: `text`

## 2. Retention Policy (ILM)
-   **Hot Phase:** 7 Days (NVMe SSD).
-   **Warm Phase:** 8-30 Days (HDD).
-   **Delete:** After 30 Days.
-   **Archive:** S3 Bucket (1 Year).

## 3. Volume & Cost
-   **Estimated Vol:** 5 GB/day (Based on 100 req/sec avg).
-   **Storage Req:** ~150 GB (Hot/Warm).
-   **Cost Impact:** Approved within P6 Budget.

## 4. Config Validation
-   [x] **Shipper:** Fluentd/Filebeat configured to parse JSON stdout.
-   [x] **Fields:** `@timestamp` mapped correctly to `timestamp` field.
-   [x] **Kibana/Dashboards:** Index Pattern created.
