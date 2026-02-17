# P23: Data Governance & GDPR Compliance

## 1. Data Classification
| Data Type | Sensitivity | Examples | Storage |
| :--- | :--- | :--- | :--- |
| **PII (Personal)** | High | Email, Phone, Device ID | `users`, `user_devices` |
| **Behavioral** | Medium | Views, Clicks, Favorites | `user_interactions`, `growth_events` |
| **Derived** | Low | Affinity Scores, Aggregates | `user_features` |
| **System** | Low | Logs, ML Metrics | `ml_prediction_logs` |

## 2. Retention Policy
To minimize liability and storage costs, we enforce hard TTL (Time-To-Live).

| Table | Retention Period | Justification |
| :--- | :--- | :--- |
| `user_interactions` | 1 Year | Analytics trends. |
| `growth_events` | 180 Days | Fraud detection window. |
| `experiment_logs` | 90 Days | A/B test duration usually < 30 days. |
| `ml_prediction_logs` | 30 Days | Debugging only. |

## 3. GDPR Rights Implementation
*   **Right to be Forgotten**: When user deletes account:
    1.  Delete `users` record (Cascades to `listings`, `devices`).
    2.  Anonymize `user_interactions` (Set `user_id = NULL`).
    3.  Delete `user_features`.

## 4. Access Control
*   **Admin Panel**: Restricted to internal IPs (VPN).
*   **Analytics Endpoints**: Require `super_admin` role.
*   **DB Backups**: Encrypted at rest.
