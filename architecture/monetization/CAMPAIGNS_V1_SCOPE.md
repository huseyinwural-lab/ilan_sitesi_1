# Campaigns V1 Scope

## Types
- individual
- corporate

## Target (single-select)
- showcase (ilan öne çıkarma)
- discount
- package

## Status
- draft
- active
- paused
- expired
- archived

## Common Rules (v1)
- discount_percent (0–100)
- discount_amount + currency_code
- min_listing_count / max_listing_count
- eligible_categories[]
- eligible_user_segment (all|new_users|returning|selected)

## Targeting (v1)
### Corporate
- eligible_dealer_plan (basic|pro|enterprise|any)
- eligible_dealers[] (optional)

### Individual
- eligible_users[] (optional)
- free_listing_quota_bonus (optional)

## Scope
- country_scope: global | country
- country_code: nullable (required when country_scope=country)

## Notes
- Single table + type field; nullable targeting fields
- V1 uses dropdown for target selection
