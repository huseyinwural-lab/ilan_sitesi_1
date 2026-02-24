# AF Sprint 1 — Migration Impact Analysis

**Amaç:** Sprint 1 guard/constraint değişikliklerinin veri etkisini ve rollback güvenliğini netleştirmek.

---

## MI-1 — Etkilenen Tablolar (Net Liste)

| Tablo | Alanlar | Not |
| --- | --- | --- |
| `users` | `risk_level` (NEW), `ban_reason` (NEW), `suspension_until` (mevcut) | `risk_level` enum (low/medium/high) ve `ban_reason` zorunlu olacak. `suspension_until` nullable kalacak ama doğrulama ile valid hale gelecek. |
| `subscription_plans` | `limits` (JSON) + **discount_percent** (NEW?) | Monetization guard’ları için min/max ve discount kontrolü gerekecek. Discount alanı mevcut değil → GAP. |
| `plans` | `listing_quota`, `showcase_quota` | Admin plan yönetimi bu tabloyu kullanıyor. Min/max constraint burada da tanımlanmalı. |
| `user_subscriptions` | `plan_id`, `status`, `current_period_*` | Plan değişimi ve quota/discount etkilerini taşır. |
| `listings` | `status`, `module`, `country` | Bulk moderation işlemleri ile ilişkilidir. |
| `audit_logs` | `action`, `metadata_info`, `resource_*` | Risk/ban/override/bulk audit’leri burada. |

---

## MI-2 — Veri Dönüşüm Analizi

### Risk Level
- **Soru:** Mevcut kayıtlarda risk_level boş mu?
- **Durum:** `risk_level` alanı yok → **default/backfill** planı şart.
- **Öneri:** Yeni alan **NOT NULL** + default `low`. Migration sırasında `low` ile backfill.

### Ban Reason
- **Soru:** Ban reason olmayan kayıt var mı?
- **Durum:** `ban_reason` alanı yok. `users.status='suspended'` kayıtları mevcut olabilir.
- **Öneri:** `ban_reason` alanını **nullable** ekle → data backfill → constraint ile NOT NULL’a yükselt.
  - Backfill önerisi: mevcut suspended kullanıcılar için `ban_reason='legacy_suspend'`.

### Discount Yüzdesi
- **Soru:** Discount % 100+ kayıt var mı?
- **Durum:** `discount_percent` alanı mevcut değil → eklenirse kontrol şart.
- **Öneri:** `CHECK (discount_percent BETWEEN 0 AND 100)`.

### Null Constraint Riski
- Yeni alanlar (risk_level, ban_reason) için **NULL** kayıtlar oluşabilir.
- Plan quota min/max constraint eklenince `listing_quota`/`showcase_quota` değerlerinin üst limitleri kontrol edilmeli.

### Pre-migration SQL Kontrol Checklist (runbook)
```sql
-- Suspended users without reason (after column added)
SELECT COUNT(*) FROM users WHERE status='suspended' AND (ban_reason IS NULL OR ban_reason='');

-- Risk level distribution (after column added)
SELECT risk_level, COUNT(*) FROM users GROUP BY risk_level;

-- Plan quota upper bound check (replace :MAX_QUOTA)
SELECT id, listing_quota, showcase_quota FROM plans
WHERE listing_quota > :MAX_QUOTA OR showcase_quota > :MAX_QUOTA;

-- Subscription plan limits sanity (JSON) (replace :MAX_QUOTA)
SELECT id, limits FROM subscription_plans
WHERE (limits->>'listing')::int > :MAX_QUOTA OR (limits->>'showcase')::int > :MAX_QUOTA;

-- Discount percent bounds (if column exists)
SELECT id, discount_percent FROM subscription_plans WHERE discount_percent < 0 OR discount_percent > 100;
```

### Data Cleanup Gereksinim Listesi
- Backfill `users.risk_level = 'low'`.
- Backfill `users.ban_reason` for suspended users.
- Normalize `subscription_plans.limits` (listing/showcase) to allowed range.
- Discount percent invalid values → clamp or reject before constraint.

---

## MI-3 — Constraint Risk Analizi

| Constraint | Runtime Hata Riski | Admin UI Etkisi | Edge Case |
| --- | --- | --- | --- |
| `users.risk_level` enum (NOT NULL) | Düşük (default/backfill) | Admin UI’da risk dropdown zorunlu | Legacy user import
| `users.ban_reason` NOT NULL (for suspended) | Orta (legacy suspended) | Suspend modal reason zorunlu | Bulk suspend legacy data
| `discount_percent` CHECK 0–100 | Orta (legacy data) | Plan formu validasyon eklenmeli | Plan import/seed
| `plans.listing_quota/showcase_quota` min/max | Orta | Plan formu min/max enforce | Existing plan > max
| `subscription_plans.limits` JSON range | Orta | Monetization panel etkilenir | JSON parse fail

---

## MI-4 — Rollback Planı

**Down script zorunlu.**
- Yeni kolonlar (`risk_level`, `ban_reason`, `discount_percent`) → rollback’te **drop column**.
- Yeni CHECK/ENUM constraint’ler → rollback’te **drop constraint/type**.
- **Veri kaybı:** Yeni kolonlarda tutulan değerler rollback’te silinir. Rollback öncesi CSV export önerilir.

Rollback sonrası stabilite:
- App-level validation fallback’e dönülür.
- Yeni alanlara bağlı UI alanları **feature flag** ile kapatılmalı.

---

## MI-5 — Deployment Strategy

1. **Migration first** (DB constraint + default/backfill)
2. **Backend deploy** (validation + guard)
3. **Admin UI deploy** (form validations + audit feedback)

**Not:** Rollback olmadan production deploy yapılmayacak.


---

## Dry-Run Checklist Mapping
Bu analizdeki kontroller `scripts/migration_dry_run.py` ile eşleştirilmiştir.

- Tablo varlık kontrolü → REQUIRED_TABLES
- Kolon tip uyumu → EXPECTED_COLUMNS
- FK integrity → user_subscriptions user/plan
- Null/enum kontrolü → risk_level / ban_reason
- Quota aralık kontrolü → plans + subscription_plans.limits
- Row count delta → snapshot diff
