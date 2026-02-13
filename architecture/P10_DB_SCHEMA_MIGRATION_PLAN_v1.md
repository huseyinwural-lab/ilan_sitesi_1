# P10 DB Schema Migration Plan

**Document ID:** P10_DB_SCHEMA_MIGRATION_PLAN_v1  
**Date:** 2026-02-13  
**Status:** 🏗️ ARCHITECTURE  

---

## 1. Overview
This migration establishes the data foundation for the Monetization Engine. It introduces Subscription Plans, User Subscriptions, and Quota Usage tracking, while extending the Listings table for Premium features.

## 2. New Tables

### 2.1. `subscription_plans`
Defines the product catalog (what users can buy).

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK | |
| `code` | String(50) | Unique, Not Null | e.g. `DEALER_TR_PRO` |
| `name` | JSON | Not Null | i18n name |
| `price` | Numeric(10,2) | Not Null | |
| `currency` | String(3) | Not Null | |
| `duration_days` | Integer | Not Null | e.g. 30 |
| `limits` | JSON | Not Null | `{"listing": 50, "showcase": 5}` |
| `is_active` | Boolean | Default True | Soft delete |

### 2.2. `user_subscriptions`
Tracks active/expired subscriptions per user.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK | |
| `user_id` | UUID | FK(users), Index | |
| `plan_id` | UUID | FK(subscription_plans) | |
| `status` | String(20) | Index | `active`, `expired`, `cancelled` |
| `start_at` | DateTime | Not Null | |
| `end_at` | DateTime | Index | Expiry date |
| `auto_renew` | Boolean | Default False | |

### 2.3. `quota_usage`
Tracks resource consumption to avoid expensive `COUNT(*)` queries on listings.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK | |
| `user_id` | UUID | FK(users), Unique(user_id, resource) | |
| `resource` | String(50) | | `listing_active`, `showcase_active` |
| `used` | Integer | Default 0 | |
| `updated_at` | DateTime | | |

## 3. Updates to Existing Tables

### 3.1. `listings`
Add Premium Feature flags.

| Column | Type | Default | Index |
|---|---|---|---|
| `is_showcase` | Boolean | False | **Composite** |
| `showcase_expires_at` | DateTime | Null | |

**New Index:** `ix_listings_cat_showcase` on `(category_id, is_showcase DESC, created_at DESC)` for Search sorting.

---

## 4. Rollback Strategy
- **Down Migration:** Drop new tables, remove columns from `listings`.
- **Data Safety:** `user_subscriptions` is critical revenue data; explicit backup required before drop.
