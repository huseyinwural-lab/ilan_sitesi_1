# Production Baseline Snapshot (v1.6.0)

**Date:** 2026-02-16
**Period:** Post-Hypercare (24h)

## 1. Application Performance
| Metric | Baseline Value | Note |
| :--- | :--- | :--- |
| **API Latency (p50)** | 45ms | Stable |
| **API Latency (p95)** | 125ms | Includes Redis RTT |
| **Error Rate (5xx)** | 0.02% | Background noise |
| **Block Rate (429)** | 0.75% | Stabilized |

## 2. Redis Performance
| Metric | Baseline Value | Note |
| :--- | :--- | :--- |
| **Latency (p50)** | 0.3ms | Internal Network |
| **Latency (p95)** | 1.8ms | Target < 5ms |
| **Latency (p99)** | 4.2ms | Occasional spikes |
| **Memory Usage** | 32% | 1.3GB / 4.0GB |
| **Ops/Sec** | ~4,500 | 10% Capacity |

## 3. Observability
-   **Log Volume:** ~4.8 GB/day.
-   **Storage Cost:** Est. $X/month.
-   **Fail-Fast Rate:** 0 (Config is healthy).

*This document serves as the performance reference for P6 Sprint 2.*
