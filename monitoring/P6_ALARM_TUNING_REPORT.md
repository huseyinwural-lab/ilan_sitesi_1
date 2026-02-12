# P6 Alarm Tuning Report

**Based on:** 48h Shadow Data

## 1. Rate Limit Spikes
-   **Old Threshold:** > 5% of traffic.
-   **Observation:** Abuse attempts spiked to 15% during attack windows, but baseline is < 0.1%.
-   **New Threshold:** > 1% (More sensitive).
-   **Reason:** Legitimate block rate is very low; 1% indicates distinct anomaly.

## 2. Redis Latency
-   **Old Threshold:** p95 > 20ms.
-   **Observation:** p95 is steady at ~2ms.
-   **New Threshold:** p95 > 10ms (Warning), > 50ms (Critical).
-   **Reason:** Tighter bound to detect degradation early.

## 3. Fail-Open Spike
-   **Threshold:** > 0 events.
-   **Action:** Keep as P1 Critical. Any Redis failure is an incident.

## 4. False Alarm Analysis
-   **Scenario:** 1 false alarm on "High Connection Usage" during deployment (pod churn).
-   **Action:** Increased Connection Alarm delay (Wait for 5m sustained usage).
