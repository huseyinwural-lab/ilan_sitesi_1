# CAMPAIGNS_SCHEMA_V1 (ADR-CAMP-01)

## Zorunlu Alanlar
- `id` (uuid)
- `name` (string)
- `status` (enum: draft | active | paused | ended)
- `start_at` (datetime)
- `end_at` (datetime | null)
- `country_code` (string, zorunlu)
- `created_at`, `updated_at`

## Opsiyonel Alanlar
- `budget_amount` (numeric | null)
- `budget_currency` (string | null) → budget_amount varsa zorunlu
- `notes` (text | null)
- `rules_json` (json | null) → hedefleme/indirim/kurallar için esnek alan

## Index Planı (V1)
- `ix_campaigns_country_status` (country_code, status)
- `ix_campaigns_start_at` (start_at)
- `ix_campaigns_end_at` (end_at)
- `ix_campaigns_created_at` (created_at)

## Notlar
- Mongo şeması birebir taşınmadı. Eksik alanlar `rules_json` ile tamponlanır.
- `end_at` null → open-ended kampanya.
