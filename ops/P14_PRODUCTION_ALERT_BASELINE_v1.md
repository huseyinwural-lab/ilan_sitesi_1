# P14 Production Alert Baseline (v1)

**Monitoring:** Prometheus + Grafana (veya Cloud Provider Dashboard)

## Aktif Alarmlar (Critical)

### 1. Ödeme Hataları (Revenue Risk)
*   **Kural:** `payment_failure_rate` > %10 (5 dk içinde).
*   **Aksiyon:** Slack #billing-alerts kanalına bildirim.

### 2. Webhook Hataları (Data Integrity Risk)
*   **Kural:** `webhook_error_total` > 0.
*   **Aksiyon:** PagerDuty (Ops ekibi).

### 3. Kupon Abuse (Fraud Risk)
*   **Kural:** `coupon_validate_fail_total` > 50/dk.
*   **Aksiyon:** IP Ban.

### 4. Referral Anormalliği (Cost Risk)
*   **Kural:** Bir kullanıcı 1 saatte > 5 ödül kazandı.
*   **Aksiyon:** Hesabı `flagged` işaretle, incelemeye al.
