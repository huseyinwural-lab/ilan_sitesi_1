# P10 Monetization Sprint Backlog

**Document ID:** P10_MONETIZATION_SPRINT_BACKLOG_v1  
**Date:** 2026-02-13  
**Sprint Goal:** Enforce limits and sell plans (Backend-first).

---

## 1. High Priority (Must Do)
- [ ] **DB Schema:** Create `subscription_plans`, `user_subscriptions`, `quota_usage` tables.
- [ ] **Data Seed:** Populate Default Plans (Basic, Pro) for TR/DE markets.
- [ ] **Quota Service:** Implement `QuotaService` class (check limit, increment).
- [ ] **Listing Create Interceptor:** Hook `POST /listings` to check Quota Service.
- [ ] **Search Update:** Implement `is_showcase` sorting logic + Index.

## 2. Medium Priority
- [ ] **Admin UI:** Page to view/cancel user subscriptions.
- [ ] **Frontend:** Pricing Page (Static display of plans).

## 3. Low Priority
- [ ] **Payment Integration:** Mock payment endpoint for testing.

---

**Estimated Effort:** 2 Weeks.
