# user_subscriptions Schema V1

## Table
`user_subscriptions`

## Required Columns
- id (uuid, PK)
- user_id (uuid, unique)
- plan_id (uuid)
- status (trial/active/past_due/canceled)
- current_period_start (datetime)
- current_period_end (datetime)
- created_at, updated_at

## Optional Columns
- provider (default: stripe)
- provider_customer_id (nullable)
- provider_subscription_id (nullable)
- canceled_at (nullable)
- meta_json (nullable)

## Foreign Keys
- user_id -> users.id
- plan_id -> plans.id
