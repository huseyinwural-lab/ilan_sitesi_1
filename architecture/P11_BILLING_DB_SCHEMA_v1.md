# P11 Billing DB Schema

**Document ID:** P11_BILLING_DB_SCHEMA_v1  
**Date:** 2026-02-13  
**Status:** 🏗️ ARCHITECTURE  

---

## 1. Tables

### 1.1. `billing_customers`
Maps local User to Stripe Customer.

| Column | Type | Constraints |
|---|---|---|
| `user_id` | UUID | PK, FK(users) |
| `stripe_customer_id` | String | Unique, Not Null |
| `balance` | Numeric | Default 0 |
| `currency` | String | Default 'TRY' |
| `created_at` | DateTime | |

### 1.2. `stripe_subscriptions`
Tracks the lifecycle of a subscription.

| Column | Type | Constraints |
|---|---|---|
| `id` | String | PK (Stripe Sub ID `sub_...`) |
| `user_id` | UUID | FK(users), Index |
| `plan_code` | String | FK(subscription_plans.code) |
| `status` | String | `active`, `past_due`, `canceled` |
| `current_period_end` | DateTime | Index |
| `cancel_at_period_end` | Boolean | Default False |
| `created_at` | DateTime | |

### 1.3. `stripe_events`
Idempotency log for Webhooks.

| Column | Type | Constraints |
|---|---|---|
| `id` | String | PK (Stripe Event ID `evt_...`) |
| `type` | String | `checkout.session.completed` |
| `processed_at` | DateTime | |
| `status` | String | `processed`, `failed` |

## 2. Relationships
- One `User` -> One `billing_customer`
- One `User` -> Many `stripe_subscriptions` (History) -> One Active

## 3. Migration Plan
- Create tables.
- Add indexes on `stripe_customer_id` and `current_period_end`.
- Grant permissions.
