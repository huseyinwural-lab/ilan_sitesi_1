# P13 Listing Expiration Job

**Document ID:** P13_LISTING_EXPIRATION_JOB_v1  
**Date:** 2026-02-13  
**Status:** ✅ COMPLETED  

---

## 1. Logic
- **Frequency:** Daily (e.g., 03:00 UTC).
- **Target:** `status='active'` AND `expires_at < NOW()`.
- **Action:**
  1. Set `status = 'expired'`.
  2. Call `QuotaService.release_quota(user_id, 'listing_active')`.
  3. If `is_showcase`, release `showcase_active` and set `is_showcase=False`.

## 2. Implementation
- Script: `scripts/process_expirations.py`.
- Execution: Cron or Kubernetes Job.

## 3. Verification
- **Test:** Created active listing with `expires_at` in past -> Run script -> Status expired, Quota released.
