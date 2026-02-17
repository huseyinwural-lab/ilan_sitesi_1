# P24: Launch Execution Plan

## Phase 1: Production Certification (Current)
- [ ] **E2E Validation**: Run `tests/e2e/validate_production_flow.py` to ensure core loop works.
- [ ] **Cold Boot**: Verify clean install (`/app/backend/scripts/recover_environment.sh`) results in usable system.
- [ ] **Rollback Drill**: Simulate a bad config push and revert it.

## Phase 2: Performance Certification
- [ ] **Load Test**: 10x traffic on `/feed` and `/recommendations`.
- [ ] **ML Latency**: Ensure P95 < 150ms under load.

## Phase 3: Security & Compliance
- [ ] **Dependency Scan**: Check `requirements.txt` for CVEs.
- [ ] **Access Audit**: Verify Admin API is protected.

## Phase 4: Operational Readiness
- [ ] **Release Tag**: Tag git `v1.0.0-rc1`.
- [ ] **Logs**: Verify `ml_prediction_logs` and `experiment_logs` are flowing.

## Phase 5: Soft Launch
- [ ] **Target**: Country `TR` only.
- [ ] **Traffic**: 100% (Single country pilot).
