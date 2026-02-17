# SPRINT0_DOMAIN_SCHEMAS_LOCK

## Amaç
FAZ-ADMIN-DOMAIN-COMPLETE-01 Sprint 0 kapsamında Mongo domain şemalarını kilitlemek.

> Karar: Dealer ayrı koleksiyon değil, `users` tabanlıdır (`role="dealer"` + `dealer_status`).

---

## 1) Dealer (users tabanlı)
**Koleksiyon:** `users`

Minimum alanlar:
- `id` (uuid)
- `email`
- `role = "dealer"`
- `dealer_status: "active" | "suspended"`
- `country_code` (dealer’ın ana ülkesi)
- `plan_id` (opsiyonel)
- `created_at`, `updated_at`

---

## 2) DealerApplication
**Koleksiyon:** `dealer_applications`

Alanlar:
- `id`
- `email`
- `company_name`
- `country_code`
- `status: pending | approved | rejected`
- `reason` (reject için): `incomplete_info | not_eligible | duplicate | other`
- `reason_note` (reason=other için zorunlu)
- `created_at`, `updated_at`

---

## 3) Invoice
**Koleksiyon:** `invoices`

Alanlar:
- `id`
- `dealer_user_id`
- `country_code`
- `status: unpaid | paid | cancelled`
- `amount_cents`
- `currency`
- `period_start`, `period_end` (opsiyonel)
- `created_at`, `updated_at`

---

## 4) TaxRate
**Koleksiyon:** `tax_rates`

Alanlar:
- `id`
- `country_code`
- `rate_percent` (0–100)
- `effective_date` (ISO date)
- `created_at`, `updated_at`

---

## 5) Plan
**Koleksiyon:** `subscription_plans`

Alanlar:
- `id`
- `name`
- `country_codes: []` (empty => global)
- `price_cents`
- `currency`
- `feature_flags: {}`
- `quota: {}`
- `is_active`
- `created_at`, `updated_at`

---

## 6) Report
**Koleksiyon:** `reports`

Alanlar:
- `id`
- `listing_id`
- `country_code`
- `status: open | in_review | closed`
- `reason` (free text)
- `note` (opsiyonel)
- `created_at`, `updated_at`

---

## 7) SystemSetting
**Koleksiyon:** `system_settings`

Alanlar:
- `id`
- `key`
- `value` (any)
- `country_code` (null => global)
- `is_read_only` (default false)
- `created_at`, `updated_at`
