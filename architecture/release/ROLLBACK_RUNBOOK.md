# P24: Rollback Runbook

## 1. Trigger Conditions (When to Rollback?)
*   **Availability**: API Error Rate > 1% for 5 minutes.
*   **Latency**: P95 Latency > 500ms for 5 minutes.
*   **Business**: Revenue drops to $0 for 1 hour.
*   **ML**: Recommendation score average drops to 0.0 (Model collapse).

## 2. Rollback Procedures

### 2.1. Config Rollback (Fastest)
If a dynamic config change (e.g., Ranking Weights) caused the issue:
1.  **Identify**: Check `audit_logs` for recent `CONFIG_CHANGE`.
2.  **Action**: Use `ConfigService` to restore previous JSON value.
3.  **Command**: `python3 scripts/restore_config.py --key ranking_weights_v1 --version previous`

### 2.2. Feature Flag Kill Switch
If a new feature (e.g., ML Ranking) is broken:
1.  **Action**: Disable Feature Flag via Admin API or DB.
2.  **SQL**: `UPDATE feature_flags SET is_enabled = false WHERE key = 'ml_ranking_v1';`
3.  **Effect**: System falls back to Rule-Based logic instantly.

### 2.3. Model Rollback
If the active ML model is performing poorly:
1.  **Action**: Activate previous model version.
2.  **SQL**:
    ```sql
    UPDATE ml_models SET is_active = false WHERE is_active = true;
    UPDATE ml_models SET is_active = true WHERE version = 'v1-stable';
    ```

### 2.4. Code/Deploy Rollback (Slowest)
If a bad code deployment occured:
1.  **Action**: Revert Git commit / Docker image tag.
2.  **Pipeline**: Trigger CI/CD rollback pipeline.
3.  **Database**: If DB migration is irreversible, stay on current DB schema but revert app code (ensure backward compatibility).
