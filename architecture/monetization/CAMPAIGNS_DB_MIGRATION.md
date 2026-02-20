# Campaigns DB Migration (V1)

## Table: campaigns

Columns:
- id (UUID, PK)
- type (individual|corporate)
- country_scope (global|country)
- country_code (nullable)
- name
- description (nullable)
- status (draft|active|paused|expired|archived)
- target (showcase|discount|package)
- start_at / end_at
- priority (low|medium|high)
- discount_percent (nullable)
- discount_amount (nullable)
- discount_currency (nullable)
- min_listing_count / max_listing_count (nullable)
- eligible_categories (JSON)
- eligible_user_segment (all|new_users|returning|selected)
- eligible_dealer_plan (basic|pro|enterprise|any)
- eligible_dealers (JSON)
- eligible_users (JSON)
- free_listing_quota_bonus (nullable)
- created_by_admin_id (FK users.id)
- created_at / updated_at

Indexes:
- type
- status
- start_at
- end_at
- country_code
- priority

## Notes
- discount_currency is derived from country_code (COUNTRY_CURRENCIES mapping)
- DB gate: endpoints return 503 DB_NOT_READY when DB not ready
