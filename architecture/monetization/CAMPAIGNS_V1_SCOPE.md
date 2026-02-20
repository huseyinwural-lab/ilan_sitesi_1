# Campaigns V1 Scope

## Types
- individual
- corporate

## Status
- draft
- active
- paused
- archived

## Package Definition
### Individual
- duration_days (>0)
- price_amount (>=0)

### Corporate
- quota_count (>0)
- price_amount (>=0)

## Common Fields
- country_scope: global | country
- country_code (nullable; required when country_scope=country)
- priority (low|medium|high)
- start_at (default now)
- end_at (optional)
- currency_code (derived from country_code; read-only in UI)

## Notes
- Single table + type field; nullable duration_days/quota_count
- V1 uses modal form with “Kaydet” and “Kaydet + Aktifleştir”
