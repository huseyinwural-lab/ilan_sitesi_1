# Operasyonel Alarm Politikası (P6)

**Scope:** Redis, Logging, Rate Limiting

## 1. Redis Alarms
| Metric | Threshold | Severity | SLA | Notification |
| :--- | :--- | :--- | :--- | :--- |
| **Latency p95** | > 20ms | Warning | 4h | Slack (Ops) |
| **Latency p95** | > 100ms | Critical | 15m | PagerDuty |
| **Conn Usage** | > 80% | Warning | 4h | Slack |
| **Error Rate** | > 1% | Critical | 15m | PagerDuty |

## 2. Rate Limit Alarms
| Metric | Threshold | Severity | SLA | Notification |
| :--- | :--- | :--- | :--- | :--- |
| **Block Rate (429)**| > 5% Total Req | Critical | 15m | PagerDuty |
| **Fail-Open Event** | > 0 | High | 1h | Slack |
| **Anomaly** | 3x Baseline Spike | Warning | 4h | Slack |

## 3. System Alarms
| Metric | Threshold | Severity | SLA | Notification |
| :--- | :--- | :--- | :--- | :--- |
| **5xx Rate** | > 1% | Critical | 15m | PagerDuty |
| **5xx Rate** | > 0.1% | Warning | 1h | Slack |
| **Pricing 409** | > 0 | Critical | 30m | PagerDuty (Revenue Risk) |
| **Circuit Breaker** | Open | Critical | 15m | PagerDuty |

## 4. Log Pipeline Alarms
| Metric | Threshold | Severity | SLA | Notification |
| :--- | :--- | :--- | :--- | :--- |
| **Ingest Lag** | > 5 min | Warning | 2h | Slack |
| **Volume** | > 2x Baseline | Warning | 4h | Slack |
