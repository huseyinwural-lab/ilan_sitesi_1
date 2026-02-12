
# P6 Sprint 2: Abuse Impact Report

**Period:** Post-Rollout 24h

## 1. Metric Improvement
-   **Standard Tier 429s:** Increased by 15% (Stricter enforcement on spammers).
-   **Premium Tier 429s:** Decreased by 90% (Correctly allowing high volume).
-   **Support Tickets:** 0 complaints from VIPs.

## 2. Bot Pattern
-   **Scraper:** Detected IP `192.168.X.X` blocked at exactly 20 req/min (Login).
-   **Burst:** Token Bucket allowed legitimate burst of 15 reqs/sec for Dealer API integration without 429.

## 3. Alarm Effectiveness
-   **Abuse Alarm:** Triggered 2 times (Correctly identified botnet).
-   **False Alarms:** 0.

**Conclusion:** Tiered Limiting successfully separates Abuse from Business Growth.
