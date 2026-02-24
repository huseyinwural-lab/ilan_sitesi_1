# AF Sprint 1 Gap List (Must-Add)

## API / Payload Gaps
- **Risk Level:** Admin update endpoint yok (ör. `PATCH /admin/users/{id}/risk-level`).
- **Verified Dealer:** Admin toggle endpoint yok (dealer_profiles.verification_status güncelleme).
- **Moderation Filters:** `GET /admin/moderation/queue` için **date range** ve **category** filtresi yok.
- **Finance Widgets UI:** `GET /admin/dashboard/summary` için frontend widget ekranı yok.

## DB / Migration Gaps
- `users.risk_level` enum (low/medium/high) alanı yok.
- Plan discount yüzdesi alanı yok (eğer UI’da kullanılacaksa `plans.discount_percent`).

## Validation / Constraint Gaps
- Plan quota min/max limitleri yok (sadece >=0). Max değerler config/constraint ile sabitlenmeli.
- Discount yüzdesi için server-side guard (0–100) yok.

## RBAC Gaps
- Risk level update için yeni permission seti yok.
- Dealer verification toggle için yeni permission seti yok.

## Audit Gaps
- Plan create/update/toggle/archival için audit event yok.
- Risk level değişimi audit event yok (`RISK_LEVEL_UPDATED`).
- Dealer verification değişimi audit event yok (`DEALER_VERIFIED`/`DEALER_UNVERIFIED`).

## Test Gaps
- Moderation filter large dataset senaryosu yok.
- Finance widget’lar için gerçek veri doğrulama testi yok.
